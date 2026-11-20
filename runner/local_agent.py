#!/usr/bin/env python3
"""Run exploratory benchmark agents through a local Ollama tool adapter.

Only approved workspace operations reach the model. This is a pilot adapter,
not a hardened OS sandbox: grading executes model-written Python locally.
"""

import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import random
import sys
import urllib.error
import urllib.request

import benchmark
import study


SYSTEM = """You are a coding agent in a small Python project. Complete the user's task. Use only the provided tools. The TASK.md request and project files are the only project evidence available to you. You may ask the simulated user and query a provider when the task describes one. Do not use hidden tests or researcher metadata. Edit the relevant project module, run visible tests, and then briefly report the result. If you cannot finish, explain why. Tool calls must use the supplied function schemas."""


TOOLS = [
    {"type": "function", "function": {"name": "list_files", "description": "List agent-visible task and project files", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read an agent-visible file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Replace one editable project Python module with complete content", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "run_tests", "description": "Run the visible project tests and return their output", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "ask_user", "description": "Ask the simulated product owner a focused requirement question", "parameters": {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]}}},
    {"type": "function", "function": {"name": "probe_provider", "description": "Query the task's provider sandbox with a JSON object; available only if described in TASK.md", "parameters": {"type": "object", "properties": {"payload": {"type": "object"}}, "required": ["payload"]}}},
]


def now():
    return datetime.now(timezone.utc).isoformat()


def emit_event(path, event):
    with path.open("a") as stream:
        stream.write(json.dumps({"time": now(), **event}, ensure_ascii=False) + "\n")


def visible_path(workspace, path):
    if not isinstance(path, str) or not path or Path(path).is_absolute():
        raise ValueError("Use a relative path inside the workspace")
    target = (workspace / path).resolve()
    if not target.is_relative_to(workspace.resolve()) or not target.is_file():
        raise ValueError("File is unavailable")
    return target


def use_tool(name, args, run, task):
    workspace = run / "workspace"
    project = workspace / "project"
    if not isinstance(args, dict):
        raise ValueError("Tool arguments must be an object")
    if name == "list_files":
        if args:
            raise ValueError("list_files takes no arguments")
        return {"files": sorted(str(p.relative_to(workspace)) for p in workspace.rglob("*") if p.is_file() and "__pycache__" not in p.parts)}
    if name == "read_file":
        if set(args) != {"path"}:
            raise ValueError("read_file requires path")
        target = visible_path(workspace, args["path"])
        return {"path": args["path"], "content": target.read_text()[:15000]}
    if name == "write_file":
        if set(args) != {"path", "content"} or not isinstance(args["content"], str):
            raise ValueError("write_file requires path and string content")
        target = visible_path(workspace, args["path"])
        if target.parent != project.resolve() or target.suffix != ".py":
            raise ValueError("Only existing top-level project Python modules are editable")
        target.write_text(args["content"])
        return {"written": args["path"], "bytes": len(args["content"].encode())}
    if name == "run_tests":
        if args:
            raise ValueError("run_tests takes no arguments")
        result = benchmark.check(project, benchmark.TASKS / task["id"] / "repo" / "tests")
        return {"passed": result["passed"], "stdout": result.get("stdout", "")[-3000:],
                "stderr": result.get("stderr", "")[-3000:], "error": result.get("error")}
    if name == "ask_user":
        if set(args) != {"question"} or not isinstance(args["question"], str):
            raise ValueError("ask_user requires question")
        with redirect_stdout(io.StringIO()) as output:
            benchmark.ask(argparse.Namespace(run=str(run), question=args["question"]))
        return json.loads(output.getvalue())
    if name == "probe_provider":
        if set(args) != {"payload"} or not isinstance(args["payload"], dict):
            raise ValueError("probe_provider requires an object payload")
        response = benchmark.provider_reply(task, args["payload"])
        benchmark.record(run, {"type": "probe", "request": args["payload"], **response})
        return response
    raise ValueError("Unknown tool")


def model_call(url, model, messages, timeout, seed):
    body = {"model": model, "stream": False, "think": False, "messages": messages, "tools": TOOLS,
            "options": {"temperature": 0, "seed": seed, "num_ctx": 8192}}
    request = urllib.request.Request(url.rstrip("/") + "/api/chat", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def run_one(args, task_id, condition, trial, group):
    run = group / f"{task_id}-{condition}-t{trial}"
    with redirect_stdout(io.StringIO()):
        study.prepare(argparse.Namespace(task=task_id, condition=condition, trial=trial, run=str(run)))
    control = run / "control"
    trace = control / "agent_trace.jsonl"
    task = benchmark.task_data(task_id)[1]
    workspace = run / "workspace"
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "system", "content": (workspace / "AGENT_INSTRUCTIONS.md").read_text()},
        {"role": "user", "content": (workspace / "TASK.md").read_text()},
    ]
    study_data = json.loads((control / "study.json").read_text())
    study_data.update({"model": args.model, "adapter": "ollama-local-tool-adapter",
                       "temperature": 0, "seed": args.seed, "max_steps": args.max_steps})
    study.write_json(control / "study.json", study_data)
    emit_event(trace, {"type": "start", "task_id": task_id, "condition": condition, "trial": trial,
                       "model": args.model, "messages": messages})
    status = "step_limit"
    error = None
    for step in range(args.max_steps):
        try:
            response = model_call(args.url, args.model, messages, args.timeout, args.seed)
            message = response["message"]
            emit_event(trace, {"type": "assistant", "step": step, "message": message,
                               "duration_ns": response.get("total_duration")})
            messages.append(message)
            calls = message.get("tool_calls") or []
            if not calls:
                status = "finished"
                break
            for call in calls:
                function = call.get("function", {})
                name = function.get("name", "")
                arguments = function.get("arguments", {})
                try:
                    result = use_tool(name, arguments, run, task)
                except (ValueError, OSError, KeyError, UnicodeError) as exc:
                    result = {"error": str(exc)}
                emit_event(trace, {"type": "tool", "step": step, "name": name,
                                   "arguments": arguments, "result": result})
                messages.append({"role": "tool", "tool_name": name, "content": json.dumps(result, ensure_ascii=False)})
        except (urllib.error.URLError, TimeoutError, OSError, KeyError, json.JSONDecodeError) as exc:
            status = "error"
            error = str(exc)
            emit_event(trace, {"type": "error", "step": step, "error": error})
            break
    with redirect_stdout(io.StringIO()) as output:
        benchmark.grade(argparse.Namespace(run=str(run)))
    grade = json.loads(output.getvalue())
    summary = {"run_path": str(run), "task_id": task_id, "category": task["category"],
               "condition": condition, "trial": trial, "model": args.model,
               "status": status, "error": error, "functional_pass": grade["functional_pass"],
               "question_count": grade["question_count"], "provider_probe_count": grade["provider_probe_count"],
               "trace_file": str(trace), "grade_file": grade["result_file"]}
    study.write_json(control / "agent_result.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen3:14b")
    parser.add_argument("--url", default="http://127.0.0.1:11434")
    parser.add_argument("--group", required=True, help="New directory under runs/ for this study")
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=16)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--seed", type=int, default=598)
    parser.add_argument("--tasks", nargs="*", help="Task IDs; defaults to all 24")
    args = parser.parse_args()
    if args.trials < 1 or args.max_steps < 1:
        parser.error("trials and max-steps must be positive")
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
    study.write_json(group / "manifest.json", {"model": args.model, "seed": args.seed,
                                                "trials": args.trials, "runs": manifest})
    summaries = []
    for index, (task_id, condition, trial) in enumerate(manifest, 1):
        print(f"[{index}/{len(manifest)}] {task_id} {condition} trial {trial}", flush=True)
        summary = run_one(args, task_id, condition, trial, group)
        summaries.append(summary)
        study.write_json(group / "agent_results.json", summaries)
        print(f"  {summary['status']} pass={summary['functional_pass']} questions={summary['question_count']} probes={summary['provider_probe_count']}", flush=True)
    print(json.dumps({"group": str(group), "runs": len(summaries),
                      "functional_passes": sum(s["functional_pass"] for s in summaries)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
