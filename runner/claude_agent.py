#!/usr/bin/env python3
"""Run benchmark agents with Claude Code inside a Docker container.

The container sees only the prepared workspace. The ask_user and
probe_provider tools are served from this process on the host, so task
metadata, private tests, and provider fixtures never enter the container.
Grading still executes agent-written Python on the host after the run.
"""

import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import random
import re
import secrets
import subprocess
import sys
import threading

import benchmark
import study


IMAGE = "clarify-bench-agent"
DOCKERFILE = Path(__file__).resolve().parent / "container" / "Dockerfile"
MOUNT = "/workspace"
AUTH_VARIABLES = ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY")
BUILTIN_TOOLS = ["Bash", "Read", "Edit", "Write", "Glob", "Grep"]
BENCH_TOOLS = ["mcp__bench__ask_user", "mcp__bench__probe_provider"]
NETWORK_PATTERN = re.compile(r"curl|wget|git\s+clone|urllib\.request|urlopen|requests|http[s]?:|socket|pip\s+install", re.I)
HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)")
WRITE_HINT = re.compile(r"\.write\(|write_text\(|open\([^)]*,\s*['\"][wa]")

PREAMBLE = """You are a coding agent in a small Python project in the current directory. The request below and the project files are the only project evidence available to you. The simulated user is the ask_user tool. A provider described in the task is the probe_provider tool: pass the provider's input as the payload object. Edit the relevant module in project/, run the visible tests, and then briefly report the result. If you cannot finish, explain why."""

MCP_TOOLS = [
    {"name": "ask_user", "description": "Ask the simulated product owner a focused requirement question",
     "inputSchema": {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]}},
    {"name": "probe_provider", "description": "Query the task's provider sandbox with a JSON object; available only if described in the task",
     "inputSchema": {"type": "object", "properties": {"payload": {"type": "object"}}, "required": ["payload"]}},
]


def now():
    return datetime.now(timezone.utc).isoformat()


def bench_tool(name, args, run, task):
    """Answer one brokered tool call and log it in the run's events."""
    if name == "ask_user":
        if set(args) != {"question"} or not isinstance(args["question"], str) or not args["question"].strip():
            raise ValueError("ask_user requires a nonempty question")
        reply = {"reply": task["user_reply"]}
        benchmark.record(run, {"type": "ask", "question": args["question"], **reply})
        return reply
    if name == "probe_provider":
        if set(args) != {"payload"} or not isinstance(args["payload"], dict):
            raise ValueError("probe_provider requires an object payload")
        reply = benchmark.provider_reply(task, args["payload"])
        benchmark.record(run, {"type": "probe", "request": args["payload"], **reply})
        return reply
    raise ValueError("Unknown tool")


class ToolHandler(BaseHTTPRequestHandler):
    """Minimal MCP server (streamable HTTP, JSON replies) exposing the two bench tools."""

    def log_message(self, *args):
        pass

    def reply(self, status, body=None):
        data = json.dumps(body).encode() if body is not None else b""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.reply(405)

    do_DELETE = do_GET

    def do_POST(self):
        target = self.server.runs.get(self.path.removeprefix("/mcp/"))
        if target is None:
            return self.reply(404)
        try:
            message = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            method = message["method"]
        except (ValueError, KeyError, TypeError):
            return self.reply(400)
        if "id" not in message:
            return self.reply(202)
        params = message.get("params") or {}
        if method == "initialize":
            result = {"protocolVersion": params.get("protocolVersion", "2025-03-26"),
                      "capabilities": {"tools": {}}, "serverInfo": {"name": "bench", "version": "1"}}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": MCP_TOOLS}
        elif method == "tools/call":
            try:
                with self.server.lock:
                    output = bench_tool(params.get("name"), params.get("arguments") or {}, *target)
                failed = False
            except (ValueError, KeyError, TypeError, UnicodeError, ArithmeticError) as error:
                output, failed = {"error": str(error)}, True
            result = {"content": [{"type": "text", "text": json.dumps(output, ensure_ascii=False)}], "isError": failed}
        else:
            return self.reply(200, {"jsonrpc": "2.0", "id": message["id"],
                                    "error": {"code": -32601, "message": "Method not found"}})
        self.reply(200, {"jsonrpc": "2.0", "id": message["id"], "result": result})


def start_tool_server(bind="127.0.0.1"):
    server = ThreadingHTTPServer((bind, 0), ToolHandler)
    server.runs = {}
    server.lock = threading.Lock()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def docker_command(args, name, workspace, prompt, tool_url):
    """The container gets one mount (the workspace) and credentials by variable name only."""
    config = {"mcpServers": {"bench": {"type": "http", "url": tool_url}}}
    command = ["docker", "run", "--rm", "--name", name,
               "--add-host", "host.docker.internal:host-gateway",
               "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
               "--memory", "2g", "--pids-limit", "256",
               "-v", f"{workspace}:{MOUNT}", "-w", MOUNT]
    for variable in AUTH_VARIABLES:
        if os.environ.get(variable):
            command += ["-e", variable]
    return command + [args.image, "claude", "-p", prompt, "--model", args.model,
                      "--output-format", "stream-json", "--verbose",
                      "--mcp-config", json.dumps(config), "--strict-mcp-config",
                      "--tools", ",".join(BUILTIN_TOOLS),
                      "--allowedTools", ",".join(BUILTIN_TOOLS + BENCH_TOOLS)]


def relative(path):
    if isinstance(path, str) and path.startswith(MOUNT + "/"):
        return path[len(MOUNT) + 1:]
    return path


def text_of(content):
    if isinstance(content, list):
        return "\n".join(block.get("text", "") for block in content if isinstance(block, dict))
    return content if isinstance(content, str) else json.dumps(content)


def workspace_files(workspace):
    """Map each workspace file name to its workspace-relative path."""
    return {path.name: str(path.relative_to(workspace)) for path in sorted(Path(workspace).rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts}


def shell_file_events(command, files):
    """Find reads and writes of known workspace files in one shell command.

    Claude Code often uses `cat file`, `cat > file <<EOF`, or `sed -i` where the
    local adapter would use read_file and write_file. This is a text heuristic:
    the command is split into steps, and a step that names a file counts as a
    write if it redirects into it, edits it in place, or is an inline script
    that writes; otherwise it counts as a read. Returns [(tool name, path)].
    """
    steps, lines, index = [], command.split("\n"), 0
    while index < len(lines):
        line = lines[index]
        index += 1
        parts = [part for part in re.split(r";|&&|\|\|", line) if part.strip()]
        marker = HEREDOC.search(line)
        if marker and parts:
            body = []
            while index < len(lines) and lines[index].strip() != marker.group(1):
                body.append(lines[index])
                index += 1
            index += 1
            # A heredoc redirected into a file is that file's new content, not commands.
            if not re.search(r">\s*[\w./-]", HEREDOC.sub("", parts[-1])):
                parts[-1] += "\n" + "\n".join(body)
        steps.extend(parts)
    found = []
    for step in steps:
        for name, path in files.items():
            mention = r"(?<![\w.-])(?:[\w.-]*/)*" + re.escape(name) + r"(?![\w.-])"
            if not re.search(mention, step):
                continue
            head = step.split("\n")[0]
            wrote = (re.search(r">>?\s*['\"]?" + mention, step)
                     or re.search(r"\b(?:sed|perl)\b[^\n]*\s-\w*i", head)
                     or re.search(r"\btee\b", head)
                     or WRITE_HINT.search(step))
            event = ("write_file" if wrote else "read_file", path)
            if event not in found[-len(files):] or wrote:
                found.append(event)
    return found


def normalize(lines, files=None):
    """Convert Claude Code stream-json into the local adapter's trace events.

    Read becomes read_file, Edit/Write become write_file, and the bench tools
    keep their names, so runner/trace_metrics.py reads both kinds of trace.
    With `files` (see workspace_files), each shell command is also followed by
    read_file/write_file events for the workspace files it touched, marked
    with "derived_from": "bash".
    Returns (events, status, error, facts about the session).
    """
    events, pending, facts = [], {}, {}
    status, error, step = "error", "No result message from Claude Code", 0
    for line in lines:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(item, dict):
            continue
        kind = item.get("type")
        if kind == "system" and item.get("subtype") == "init":
            facts = {key: item.get(key) for key in ("model", "claude_code_version", "tools", "mcp_servers")}
        elif kind == "assistant":
            content = item.get("message", {}).get("content", [])
            events.append({"type": "assistant", "step": step, "message": {"content": content}})
            for block in content:
                if block.get("type") == "tool_use":
                    pending[block["id"]] = (step, block["name"], block.get("input") or {})
            step += 1
        elif kind == "user":
            content = item.get("message", {}).get("content", [])
            for block in content if isinstance(content, list) else []:
                if block.get("type") != "tool_result" or block.get("tool_use_id") not in pending:
                    continue
                at, name, arguments = pending.pop(block["tool_use_id"])
                output = text_of(block.get("content"))
                if name in ("Read", "Edit", "Write"):
                    arguments = {**arguments, "path": relative(arguments.get("file_path"))}
                    name = "read_file" if name == "Read" else "write_file"
                elif name in BENCH_TOOLS:
                    name = name.removeprefix("mcp__bench__")
                else:
                    name = name.lower()
                if block.get("is_error"):
                    result = {"error": output}
                elif name in ("ask_user", "probe_provider"):
                    try:
                        result = json.loads(output)
                    except json.JSONDecodeError:
                        result = {"output": output}
                else:
                    result = {"output": output[:15000]}
                events.append({"type": "tool", "step": at, "name": name, "arguments": arguments, "result": result})
                if name == "bash" and files:
                    for derived, path in shell_file_events(arguments.get("command", ""), files):
                        events.append({"type": "tool", "step": at, "name": derived, "arguments": {"path": path},
                                       "result": {"derived_from": "bash"}})
        elif kind == "result":
            facts.update({key: item.get(key) for key in ("num_turns", "duration_ms", "total_cost_usd")})
            events.append({"type": "result", "subtype": item.get("subtype"), "result": item.get("result")})
            if item.get("subtype") == "success" and not item.get("is_error"):
                status, error = "finished", None
            elif item.get("subtype") == "error_max_turns":
                status, error = "step_limit", None
            else:
                status, error = "error", str(item.get("result") or item.get("subtype"))
    return events, status, error, facts


def network_commands(events):
    """Shell commands that look like network use. The container still has internet access."""
    return [event["arguments"].get("command", "") for event in events
            if event.get("type") == "tool" and event["name"] == "bash"
            and NETWORK_PATTERN.search(event["arguments"].get("command", ""))]


def write_trace(trace, start, events):
    with trace.open("w") as stream:
        for event in [start] + [{"time": now(), **event} for event in events]:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")


def rebuild(group):
    """Rewrite each run's agent_trace.jsonl from its saved claude_stream.jsonl."""
    group = Path(group).resolve()
    summaries = json.loads((group / "agent_results.json").read_text())
    for summary in summaries:
        run = group / Path(summary["run_path"]).name
        trace = run / "control" / "agent_trace.jsonl"
        start = json.loads(trace.read_text().splitlines()[0])
        stream = (run / "control" / "claude_stream.jsonl").read_text().splitlines()
        events = normalize(stream, workspace_files(run / "workspace"))[0]
        write_trace(trace, start, events)
        summary["network_commands"] = network_commands(events)
        summary["trace_file"] = str(trace)
        study.write_json(run / "control" / "agent_result.json", summary)
    study.write_json(group / "agent_results.json", summaries)
    print(json.dumps({"group": str(group), "rebuilt_traces": len(summaries)}, indent=2))


def run_one(args, server, task_id, condition, trial, group):
    run = group / f"{task_id}-{condition}-t{trial}"
    with redirect_stdout(io.StringIO()):
        study.prepare(argparse.Namespace(task=task_id, condition=condition, trial=trial, run=str(run)))
    control, workspace = run / "control", run / "workspace"
    task = benchmark.task_data(task_id)[1]
    prompt = "\n\n".join([PREAMBLE, (workspace / "AGENT_INSTRUCTIONS.md").read_text().strip(),
                          (workspace / "TASK.md").read_text().strip()])
    token = secrets.token_urlsafe(24)
    server.runs[token] = (run, task)
    name = f"clarify-bench-{secrets.token_hex(6)}"
    command = docker_command(args, name, workspace, prompt,
                             f"http://host.docker.internal:{server.server_address[1]}/mcp/{token}")
    started = now()
    try:
        process = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                 timeout=args.timeout)
        stdout, stderr, timed_out = process.stdout, process.stderr, False
    except subprocess.TimeoutExpired as expired:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        stdout, stderr, timed_out = expired.stdout or "", expired.stderr or "", True
        stdout = stdout.decode() if isinstance(stdout, bytes) else stdout
        stderr = stderr.decode() if isinstance(stderr, bytes) else stderr
    finally:
        del server.runs[token]
    (control / "claude_stream.jsonl").write_text(stdout)
    events, status, error, facts = normalize(stdout.splitlines(), workspace_files(workspace))
    if timed_out:
        status, error = "step_limit", f"Run exceeded {args.timeout} seconds"
    elif status == "error" and stderr.strip():
        error = f"{error}: {stderr.strip()[-500:]}"
    trace = control / "agent_trace.jsonl"
    start = {"time": started, "type": "start", "task_id": task_id, "condition": condition, "trial": trial,
             "model": facts.get("model") or args.model, "prompt": prompt}
    write_trace(trace, start, events)
    study_data = json.loads((control / "study.json").read_text())
    study_data.update({"model": facts.get("model") or args.model, "adapter": "claude-code-docker",
                       "claude_code_version": facts.get("claude_code_version"), "image": args.image,
                       "timeout": args.timeout, "builtin_tools": BUILTIN_TOOLS})
    study.write_json(control / "study.json", study_data)
    with redirect_stdout(io.StringIO()) as output:
        benchmark.grade(argparse.Namespace(run=str(run)))
    grade = json.loads(output.getvalue())
    summary = {"run_path": str(run), "task_id": task_id, "category": task["category"],
               "condition": condition, "trial": trial, "model": study_data["model"],
               "status": status, "error": error, "functional_pass": grade["functional_pass"],
               "question_count": grade["question_count"], "provider_probe_count": grade["provider_probe_count"],
               "network_commands": network_commands(events), "num_turns": facts.get("num_turns"),
               "trace_file": str(trace), "grade_file": grade["result_file"]}
    study.write_json(control / "agent_result.json", summary)
    return summary


def docker(*arguments):
    return subprocess.run(["docker", *arguments], capture_output=True, text=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="claude-sonnet-5-5")
    parser.add_argument("--group", help="New directory under runs/ for this study")
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=600, help="Seconds allowed per run")
    parser.add_argument("--seed", type=int, default=598, help="Seed for condition order")
    parser.add_argument("--tasks", nargs="*", help="Task IDs; defaults to all 24")
    parser.add_argument("--image", default=IMAGE)
    parser.add_argument("--bind", default="127.0.0.1",
                        help="Tool server address; use 0.0.0.0 on Linux Docker Engine")
    parser.add_argument("--build", action="store_true", help="Build the container image and exit")
    parser.add_argument("--rebuild", metavar="GROUP",
                        help="Rewrite a finished group's traces from the saved Claude Code output and exit")
    args = parser.parse_args()
    if args.rebuild:
        rebuild(args.rebuild)
        return 0
    if args.build:
        return subprocess.run(["docker", "build", "-t", args.image, str(DOCKERFILE.parent)]).returncode
    if not args.group:
        parser.error("--group is required")
    if args.trials < 1 or args.timeout < 1:
        parser.error("trials and timeout must be positive")
    if not any(os.environ.get(variable) for variable in AUTH_VARIABLES):
        parser.error("Set CLAUDE_CODE_OAUTH_TOKEN (from `claude setup-token`) or ANTHROPIC_API_KEY")
    if docker("image", "inspect", args.image).returncode != 0:
        parser.error(f"Image {args.image} not found or Docker is not running; run with --build first")
    group = Path(args.group).resolve()
    if group.exists():
        parser.error("Group directory already exists; use a fresh name")
    group.mkdir(parents=True)
    tasks = args.tasks or sorted(path.parent.name for path in benchmark.TASKS.glob("*/task.json"))
    randomizer = random.Random(args.seed)
    manifest = []
    for trial in range(1, args.trials + 1):
        for task_id in tasks:
            benchmark.task_data(task_id)
            conditions = list(study.CONDITIONS)
            randomizer.shuffle(conditions)
            manifest.extend((task_id, condition, trial) for condition in conditions)
    version = docker("run", "--rm", args.image, "claude", "--version").stdout.strip()
    study.write_json(group / "manifest.json", {"model": args.model, "seed": args.seed, "trials": args.trials,
                                                "adapter": "claude-code-docker", "claude_code": version,
                                                "runs": manifest})
    server = start_tool_server(args.bind)
    summaries = []
    for index, (task_id, condition, trial) in enumerate(manifest, 1):
        print(f"[{index}/{len(manifest)}] {task_id} {condition} trial {trial}", flush=True)
        summary = run_one(args, server, task_id, condition, trial, group)
        summaries.append(summary)
        study.write_json(group / "agent_results.json", summaries)
        print(f"  {summary['status']} pass={summary['functional_pass']} questions={summary['question_count']} probes={summary['provider_probe_count']}", flush=True)
        if summary["status"] == "error":
            print(f"  error: {summary['error']}", flush=True)
    print(json.dumps({"group": str(group), "runs": len(summaries),
                      "functional_passes": sum(s["functional_pass"] for s in summaries)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
