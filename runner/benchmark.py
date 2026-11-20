#!/usr/bin/env python3
"""Local pilot task preparation, manual tool brokering, and functional grading."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "benchmarks"


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def emit(value):
    print(json.dumps(value, indent=2))


def task_data(task_id):
    if not re.fullmatch(r"(?:act|explore|experiment|ask)_\d{3}", task_id):
        raise ValueError("Invalid task ID")
    directory = TASKS / task_id
    return directory, json.loads((directory / "task.json").read_text())


def load_run(run):
    run = Path(run).resolve()
    state = json.loads((run / "control" / "run.json").read_text())
    directory, task = task_data(state["task_id"])
    return run, state, directory, task


def record(run, event):
    with (run / "control" / "events.jsonl").open("a") as stream:
        stream.write(json.dumps({"time": timestamp(), **event}) + "\n")


def prepare(args):
    directory, task = task_data(args.task)
    run = Path(args.run).resolve()
    # Refuse any existing destination, even an empty one.
    run.mkdir(parents=True, exist_ok=False)
    (run / "control").mkdir()
    (run / "workspace").mkdir()
    shutil.copytree(directory / "repo", run / "workspace" / "project")
    shutil.copyfile(directory / "prompt.md", run / "workspace" / "TASK.md")
    state = {"task_id": task["id"], "created_at": timestamp(), "run_path": str(run)}
    (run / "control" / "run.json").write_text(json.dumps(state, indent=2) + "\n")
    (run / "control" / "events.jsonl").touch()
    emit({"workspace": str(run / "workspace"), "researcher_control": str(run / "control"),
          "note": "Expose only workspace and approved tool replies to the agent."})


def ask(args):
    run, _, _, task = load_run(args.run)
    if not args.question.strip():
        raise ValueError("Question must not be empty")
    reply = {"reply": task["user_reply"]}
    record(run, {"type": "ask", "question": args.question, **reply})
    emit(reply)


def probe(args):
    run, _, _, task = load_run(args.run)
    if "provider_rounding" not in task:
        raise ValueError("The provider tool is not available for this task")
    if not re.fullmatch(r"[+-]?\d{1,12}(?:\.\d{1,6})?", args.amount):
        raise ValueError("Use a decimal string with <=12 integer and <=6 fractional digits")
    with localcontext() as context:
        context.prec = 32
        value = Decimal(args.amount).quantize(Decimal("0.01"), rounding=task["provider_rounding"])
    if value == 0:
        value = abs(value)
    reply = {"amount": args.amount, "rounded": format(value, ".2f")}
    record(run, {"type": "probe", **reply})
    emit(reply)


def check(project, tests):
    # Final tests remain outside the agent workspace. This is NOT an OS sandbox.
    script = (
        "import sys, unittest; "
        "sys.path.insert(0, sys.argv[1]); "
        "suite = unittest.defaultTestLoader.discover(sys.argv[2]); "
        "result = unittest.TextTestRunner(verbosity=2).run(suite); "
        "sys.exit(0 if result.wasSuccessful() else 1)"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-B", "-c", script, str(project), str(tests)],
            cwd=project, capture_output=True, text=True, timeout=20,
        )
        return {"passed": result.returncode == 0, "exit_code": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired:
        return {"passed": False, "error": "Test process exceeded 20 seconds"}


def grade(args):
    run, state, directory, task = load_run(args.run)
    project = run / "workspace" / "project"
    visible = check(project, project / "tests")
    final = check(project, directory / "private_tests")
    events = [json.loads(line) for line in (run / "control" / "events.jsonl").read_text().splitlines() if line.strip()]
    result = {
        "task_id": task["id"], "status": task["status"], "graded_at": timestamp(),
        "run_path": str(run), "functional_pass": visible["passed"] and final["passed"],
        "question_count": sum(event["type"] == "ask" for event in events),
        "provider_probe_count": sum(event["type"] == "probe" for event in events),
        "visible_tests": visible, "final_tests": final,
        "behavioral_score": None,
        "note": "Functional success does not establish correct investigation or necessary questions. Review full tool traces.",
    }
    output = ROOT / "results"
    output.mkdir(exist_ok=True)
    key = hashlib.sha256(str(run).encode()).hexdigest()[:10]
    filename = output / f"{task['id']}-{key}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}.json"
    filename.write_text(json.dumps(result, indent=2) + "\n")
    emit({**result, "result_file": str(filename)})
    return 0 if result["functional_pass"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List researcher-facing task metadata")
    p = sub.add_parser("prepare", help="Copy a task into a new run workspace")
    p.add_argument("task")
    p.add_argument("--run", required=True)
    p = sub.add_parser("ask", help="Broker a simulated-user question")
    p.add_argument("--run", required=True)
    p.add_argument("--question", required=True)
    p = sub.add_parser("probe", help="Query the rounding provider sandbox")
    p.add_argument("--run", required=True)
    p.add_argument("--amount", required=True)
    p = sub.add_parser("grade", help="Run visible/final functional checks and save JSON results")
    p.add_argument("--run", required=True)
    args = parser.parse_args()
    try:
        if args.command == "list":
            emit([json.loads(p.read_text()) for p in sorted(TASKS.glob("*/task.json"))])
        elif args.command == "prepare":
            prepare(args)
        elif args.command == "ask":
            ask(args)
        elif args.command == "probe":
            probe(args)
        else:
            return grade(args)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        parser.exit(2, f"error: {error}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
