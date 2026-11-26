"""Relay a two-condition follow-up through fresh ChatGPT conversations."""

import argparse
from collections import Counter
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import random
import sys

import benchmark
import local_agent
import study
import trace_metrics


CONDITIONS = ("standard", "evidence_policy")
POLICY = (
    "Before implementing behavior that depends on a missing fact, identify what you "
    "need to know. If the request or repository answers it, use that evidence. "
    "If two technical behaviors are plausible, predict what each would return for "
    "the same input and probe an input where the predictions differ. If the "
    "decision is a product preference that technical evidence cannot settle, ask "
    "one focused question before implementing that behavior. Then implement and verify."
)
RELAY = """
Reply with exactly one JSON object per turn, without Markdown. Use
{"name":"tool_name","arguments":{...}} to call a tool. Optional "note" may
briefly state your plan or what a probe would distinguish. Wait for its JSON
result before taking your next action. Use {"name":"finish","arguments":{"summary":"..."}}
when done. This chat relays all tool calls. Only use the following tools.
""".strip()


def snapshot(path):
    return json.loads(path.read_text())


def prepare(args):
    group = Path(args.group).resolve()
    if not args.model.strip() or args.max_steps < 1:
        raise ValueError("Specify a model label and a positive turn limit")
    if len(set(args.tasks or [])) != len(args.tasks or []):
        raise ValueError("Specify each task once")
    tasks = args.tasks or sorted(p.parent.name for p in benchmark.TASKS.glob("*/task.json"))
    for task in tasks:
        benchmark.task_data(task)
    group.mkdir(parents=True, exist_ok=False)
    rng = random.Random(args.seed)
    schedule = []
    for task in tasks:
        conditions = list(CONDITIONS)
        rng.shuffle(conditions)
        for condition in conditions:
            # Opaque IDs prevent the folder name from giving away the category.
            run_id = f"run-{len(schedule) + 1:02d}"
            run = group / run_id
            schedule.append({"run": run_id, "task_id": task, "condition": condition})
            with redirect_stdout(io.StringIO()):
                benchmark.prepare(argparse.Namespace(task=task, run=run))
            workspace = run / "workspace"
            tools = [t["function"] for t in local_agent.TOOLS]
            descriptions = "\n".join(
                json.dumps(tool, ensure_ascii=False) for tool in tools
            )
            parts = [local_agent.SYSTEM, study.CONDITIONS["standard"], RELAY, descriptions]
            if condition == "evidence_policy":
                parts.append(POLICY)
            parts.append((workspace / "TASK.md").read_text().strip())
            prompt = "\n\n".join(parts) + "\n"
            (workspace / "CHAT_PROMPT.txt").write_text(prompt)
            control = run / "control"
            study.write_json(control / "study.json", {
                "task_id": task, "condition": condition, "trial": 1,
                "model": args.model, "max_steps": args.max_steps,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            })
    study.write_json(group / "manifest.json", {
        "model": args.model, "max_steps": args.max_steps, "seed": args.seed,
        "runs": schedule,
    })
    benchmark.emit({"group": str(group), "prepared": len(schedule), "first": str(group / "run-01")})


def relay(args):
    run, _, _, task = benchmark.load_run(args.run)
    control = run / "control"
    settings = snapshot(control / "study.json")
    trace = control / "agent_trace.jsonl"
    pasted = args.reply.strip()
    prompt = (run / "workspace" / "CHAT_PROMPT.txt").read_text()
    if not pasted or pasted.startswith("pbpaste |") or pasted == prompt.strip():
        raise ValueError("Copy the ChatGPT reply first, then type the relay command in Terminal")
    if (control / "agent_result.json").exists():
        raise ValueError("This run is already graded")
    if not trace.exists():
        if hashlib.sha256(prompt.encode()).hexdigest() != settings["prompt_sha256"]:
            raise ValueError("Prepared prompt changed")
        local_agent.emit_event(trace, {"type": "start", **settings, "prompt": prompt})
    events = [json.loads(line) for line in trace.read_text().splitlines()]
    if any(event["type"] == "result" for event in events):
        raise ValueError("This run has finished; grade it next")
    step = sum(event["type"] == "assistant" for event in events)
    if step >= settings["max_steps"]:
        raise ValueError("Turn limit reached; grade the current workspace")
    local_agent.emit_event(trace, {"type": "assistant", "step": step, "message": args.reply})
    try:
        reply = json.loads(args.reply)
        if not isinstance(reply, dict) or set(reply) - {"name", "arguments", "note"}:
            raise ValueError("Expected one object with name, arguments and optional note")
        name, payload = reply["name"], reply["arguments"]
        if name == "finish":
            if not isinstance(payload, dict) or set(payload) != {"summary"} or not isinstance(payload["summary"], str):
                raise ValueError("finish requires a string summary")
            local_agent.emit_event(trace, {"type": "result", "summary": payload["summary"]})
            benchmark.emit({"finished": True})
            return
        result = local_agent.use_tool(name, payload, run, task)
    except (ValueError, OSError, KeyError, TypeError) as error:
        result = {"error": str(error)}
        if "name" not in locals():
            name, payload = "invalid_reply", {}
    local_agent.emit_event(trace, {
        "type": "tool", "step": step, "name": name, "arguments": payload, "result": result,
    })
    benchmark.emit(result)


def grade(args):
    run, _, _, task = benchmark.load_run(args.run)
    control = run / "control"
    settings = snapshot(control / "study.json")
    trace = control / "agent_trace.jsonl"
    if not trace.exists():
        raise ValueError("Relay at least one actual model reply before grading")
    events = [json.loads(line) for line in trace.read_text().splitlines()]
    finished = any(event["type"] == "result" for event in events)
    turns = sum(event["type"] == "assistant" for event in events)
    if not finished and turns < settings["max_steps"]:
        raise ValueError("Grade after the model finishes or reaches the turn limit")
    with redirect_stdout(io.StringIO()) as output:
        benchmark.grade(argparse.Namespace(run=run))
    checks = json.loads(output.getvalue())
    result = {
        **settings, "category": task["category"], "turns": turns,
        "run_path": str(run), "trace_file": str(trace),
        "status": "finished" if finished else "step_limit",
        **{key: checks[key] for key in ("functional_pass", "question_count", "provider_probe_count")},
    }
    result.update({
        key: value for key, value in trace_metrics.one_run(result).items()
        if key in ("source_evidence", "functional_with_evidence", "evidence")
    })
    study.write_json(control / "agent_result.json", result)
    benchmark.emit(result)


def summarize(args):
    group = Path(args.group)
    manifest = snapshot(group / "manifest.json")
    completed = []
    for entry in manifest["runs"]:
        path = group / entry["run"] / "control" / "agent_result.json"
        if path.is_file():
            completed.append(snapshot(path))
    counts = Counter(row["task_id"] for row in completed)
    paired = [row for row in completed if counts[row["task_id"]] == len(CONDITIONS)]
    metrics = ("functional_pass", "source_evidence", "functional_with_evidence", "question_count", "provider_probe_count")
    def totals(rows):
        return {"runs": len(rows), **{key: sum(row[key] for row in rows) for key in metrics}}
    summary = {
        "model": manifest["model"], "scheduled_runs": len(manifest["runs"]),
        "graded_runs": len(completed), "complete_pairs": len(paired) // 2,
        "conditions": {},
    }
    for condition in CONDITIONS:
        rows = [row for row in paired if row["condition"] == condition]
        summary["conditions"][condition] = {
            **totals(rows),
            "by_category": {category: totals([row for row in rows if row["category"] == category])
                            for category in ("act", "explore", "experiment", "ask")},
        }
    study.write_json(group / "summary.json", summary)
    benchmark.emit(summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    cmd = commands.add_parser("prepare")
    cmd.add_argument("--group", required=True)
    cmd.add_argument("--model", required=True, help="Exact model label chosen in the app")
    cmd.add_argument("--max-steps", type=int, default=12)
    cmd.add_argument("--seed", type=int, default=598)
    cmd.add_argument("--tasks", nargs="+")
    cmd = commands.add_parser("relay")
    cmd.add_argument("--run", required=True)
    cmd.add_argument("--reply", help="Model's verbatim JSON reply; defaults to stdin")
    cmd = commands.add_parser("grade")
    cmd.add_argument("--run", required=True)
    cmd = commands.add_parser("summarize")
    cmd.add_argument("--group", required=True)
    args = parser.parse_args()
    if args.command == "relay" and args.reply is None:
        args.reply = sys.stdin.read()
    try:
        {"prepare": prepare, "relay": relay, "grade": grade, "summarize": summarize}[args.command](args)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
