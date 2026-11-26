"""Run both follow-up conditions using the OpenAI API or signed-in Codex."""

import argparse
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
from shutil import which
from tempfile import TemporaryDirectory
import urllib.error
import urllib.request

import chatgpt_followup as followup
import local_agent
import study


ENDPOINT = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-6.2-sol"
BUNDLED_CODEX = Path(
    "/Applications/ChatGPT.app/Contents/Resources/codex-cli/"
    "CodexCLI.app/Contents/MacOS/codex"
)


def find_codex():
    cli = which("codex")
    if cli:
        return str(Path(cli).resolve())
    if BUNDLED_CODEX.is_file() and os.access(BUNDLED_CODEX, os.X_OK):
        return str(BUNDLED_CODEX)
    raise ValueError("Codex CLI not found on PATH or in the ChatGPT app under /Applications")


def request_reply(key, settings, messages):
    body = {
        "model": settings["model"],
        "reasoning": {"effort": settings["effort"]},
        "max_output_tokens": settings["max_output_tokens"],
        "store": False,
        "input": messages,
        "text": {"format": {"type": "json_object"}},
    }
    request = urllib.request.Request(
        ENDPOINT, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as connection:
            response = json.load(connection)
    except urllib.error.HTTPError as error:
        try:
            message = json.load(error)["error"]["message"]
        except (ValueError, KeyError, TypeError):
            message = error.reason
        raise ValueError(f"OpenAI HTTP {error.code}: {message}") from None
    if response.get("status") != "completed":
        raise ValueError(f"API response was {response.get('status')}: {response.get('incomplete_details')}")
    reply = "\n".join(
        part["text"]
        for item in response["output"] if item["type"] == "message"
        for part in item["content"] if part["type"] == "output_text"
    )
    if not reply.strip():
        raise ValueError("API returned no agent reply")
    return reply, {
        "type": "api_response", "response_id": response["id"],
        "model": response["model"], "usage": response.get("usage"),
    }


def codex_reply(settings, messages, executable):
    # Replay only this task's conversation in a scratch directory. All benchmark
    # actions are handled by the same relay used by the API backend.
    with TemporaryDirectory(prefix="clarify-codex-") as directory:
        output = Path(directory) / "reply.txt"
        command = [
            executable, "-a", "never", "exec", "--ignore-user-config",
            "--ephemeral", "--skip-git-repo-check", "--sandbox", "read-only",
            "--disable", "shell_tool", "--disable", "unified_exec",
            "-c", 'web_search="disabled"',
            "-c", f'model_reasoning_effort="{settings["effort"]}"',
            "--model", settings["model"], "--output-last-message", str(output), "-",
        ]
        prompt = messages[0]["content"]
        if len(messages) > 1:
            history = json.dumps(messages[1:], ensure_ascii=False)
            prompt += "\n\nContinue the transcript below with the next requested JSON object.\n" + history
        try:
            result = subprocess.run(
                command, cwd=directory, input=prompt, capture_output=True,
                text=True, timeout=180,
                env={k: v for k, v in os.environ.items() if k not in
                     {"OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL"}},
            )
        except subprocess.TimeoutExpired:
            raise ValueError("Codex CLI timed out during a model turn") from None
        if result.returncode != 0:
            raise ValueError(f"Codex CLI exited {result.returncode}: {result.stderr.strip()[-2000:]}")
        reply = output.read_text().strip()
    lines = reply.splitlines()
    if len(lines) >= 3 and lines[0] in ("```json", "```") and lines[-1] == "```":
        reply = "\n".join(lines[1:-1])
    if not reply:
        raise ValueError("Codex CLI returned an empty reply")
    return reply, {"type": "codex_response", "requested_model": settings["model"]}


def run_one(run, settings, get_reply):
    trace = run / "control" / "agent_trace.jsonl"
    prompt = (run / "workspace" / "CHAT_PROMPT.txt").read_text()
    metadata_path = run / "control" / "study.json"
    if hashlib.sha256(prompt.encode()).hexdigest() != followup.snapshot(metadata_path)["prompt_sha256"]:
        raise ValueError(f"Prepared prompt changed in {run}")
    messages = [{"role": "user", "content": prompt}]
    finished = False
    events = [json.loads(line) for line in trace.read_text().splitlines()] if trace.exists() else []
    for event in events:
        if event["type"] == "assistant":
            messages.append({"role": "assistant", "content": event["message"]})
        elif event["type"] == "tool":
            messages.append({"role": "user", "content": json.dumps(event["result"])})
        elif event["type"] == "result":
            finished = True
    if not finished and len(messages) % 2 == 0:
        raise ValueError(f"Incomplete local tool trace in {run}; inspect it before resuming")
    turns = len(messages) // 2
    # Only prior assistant replies and broker outputs from this run are replayed.
    while not finished and turns < settings["max_steps"]:
        reply, metadata = get_reply(settings, messages)
        with redirect_stdout(io.StringIO()) as output:
            followup.relay(argparse.Namespace(run=run, reply=reply))
        result = json.loads(output.getvalue())
        local_agent.emit_event(trace, metadata)
        messages.extend([
            {"role": "assistant", "content": reply},
            {"role": "user", "content": json.dumps(result)},
        ])
        turns += 1
        finished = result == {"finished": True}
    with redirect_stdout(io.StringIO()) as output:
        followup.grade(argparse.Namespace(run=run))
    return json.loads(output.getvalue())


def run_batch(args, get_reply):
    group = Path(args.group).resolve()
    config_path = group / ("codex-settings.json" if args.backend == "codex" else "openai-settings.json")
    settings = {
        "model": args.model, "effort": args.effort, "max_steps": args.max_steps,
        "max_output_tokens": args.max_output_tokens, "seed": args.seed,
        "tasks": args.tasks,
    }
    if group.exists():
        if not config_path.is_file() or followup.snapshot(config_path) != settings:
            raise ValueError("Use a new output directory or resume with the original command and settings")
    else:
        followup.prepare(args)
        study.write_json(config_path, settings)
    schedule = followup.snapshot(group / "manifest.json")["runs"]
    for index, entry in enumerate(schedule, 1):
        run = group / entry["run"]
        if (run / "control" / "agent_result.json").exists():
            continue
        print(f"[{index}/{len(schedule)}] {entry['task_id']} {entry['condition']}", flush=True)
        # Keep API configuration in the per-run result alongside its prompt hash.
        path = run / "control" / "study.json"
        study.write_json(path, {**followup.snapshot(path), "adapter": "codex-cli-relay" if args.backend == "codex" else "openai-responses-json",
                                "reasoning_effort": args.effort, "max_output_tokens": args.max_output_tokens})
        result = run_one(run, settings, get_reply)
        print(f"  passed={result['functional_pass']} evidence={result['source_evidence']}"
              f" questions={result['question_count']} probes={result['provider_probe_count']}", flush=True)
    followup.summarize(argparse.Namespace(group=group))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", required=True)
    parser.add_argument("--backend", choices=("api", "codex"), default="api")
    parser.add_argument("--model")
    parser.add_argument("--effort", default="low", choices=("low", "medium", "high"))
    parser.add_argument("--max-steps", type=int, default=12)
    parser.add_argument("--max-output-tokens", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=598)
    parser.add_argument("--tasks", nargs="+", help="Defaults to all 24 benchmark tasks")
    args = parser.parse_args()
    if args.max_steps < 1 or args.max_output_tokens < 1:
        parser.error("Limits must be positive")
    args.model = args.model or ("gpt-6.1-sol" if args.backend == "codex" else DEFAULT_MODEL)
    # Subprocesses executing benchmark code should not inherit the API key.
    key = os.environ.pop("OPENAI_API_KEY", "").strip()
    if args.backend == "api":
        if not key:
            parser.error("Set OPENAI_API_KEY in your terminal first")
        get_reply = lambda settings, messages: request_reply(key, settings, messages)
    try:
        if args.backend == "codex":
            executable = find_codex()
            status = subprocess.run([executable, "login", "status"], capture_output=True, text=True)
            get_reply = lambda settings, messages: codex_reply(settings, messages, executable)
            if status.returncode != 0 or "Logged in using ChatGPT" not in status.stdout + status.stderr:
                raise ValueError("Sign in to the Codex CLI with ChatGPT using codex login")
        run_batch(args, get_reply)
    except KeyboardInterrupt:
        parser.exit(130, "\nInterrupted. Rerun the same command to resume.\n")
    except (OSError, ValueError, KeyError) as error:
        message = str(error).replace(key, "[redacted]") if key else str(error)
        parser.exit(1, f"error: {message}\n")


if __name__ == "__main__":
    main()
