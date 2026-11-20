#!/usr/bin/env python3
"""Prepare balanced pilot runs and summarize trace-reviewed agent outcomes.

This is a researcher-side tool. It deliberately does not launch an agent or
claim that a passing implementation demonstrates a correct decision.
"""

import argparse
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys

import benchmark


CONDITIONS = {
    "standard": """Complete TASK.md in project/. You may inspect the project, run its tests, ask the simulated user, and probe any provider tool described in the task. Make the requested change and report what you did.""",
    "ask_when_unsure": """Complete TASK.md in project/. You may inspect the project, run its tests, ask the simulated user, and probe any provider tool described in the task. Ask the simulated user when you are unsure about a requirement. Make the requested change and report what you did.""",
    "decision_policy": """Complete TASK.md in project/. You may inspect the project, run its tests, ask the simulated user, and probe any provider tool described in the task. Before settling an uncertain detail, identify its source: the request itself, existing project evidence, a safe provider probe, or a product decision only the user can make. Use that source to resolve the detail, then implement and test the change. Ask a focused question when only the user can decide. Report what you did.""",
}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def prepare(args):
    run = Path(args.run).resolve()
    if args.condition not in CONDITIONS:
        raise ValueError("Unknown condition")
    if args.trial < 1:
        raise ValueError("Trial must be positive")
    with redirect_stdout(io.StringIO()):
        benchmark.prepare(argparse.Namespace(task=args.task, run=str(run)))
    instructions = CONDITIONS[args.condition] + "\n"
    (run / "workspace" / "AGENT_INSTRUCTIONS.md").write_text(instructions)
    prompt = (run / "workspace" / "TASK.md").read_bytes()
    write_json(run / "control" / "study.json", {
        "condition": args.condition,
        "trial": args.trial,
        "task_id": args.task,
        "task_prompt_sha256": hashlib.sha256(prompt).hexdigest(),
        "condition_prompt_sha256": hashlib.sha256(instructions.encode()).hexdigest(),
    })
    print(json.dumps({"workspace": str(run / "workspace"), "condition": args.condition,
                      "trial": args.trial, "researcher_control": str(run / "control")}, indent=2))


def review(args):
    run, _, _, task = benchmark.load_run(args.run)
    study = json.loads((run / "control" / "study.json").read_text())
    for filename, expected in (("TASK.md", study["task_prompt_sha256"]),
                               ("AGENT_INSTRUCTIONS.md", study["condition_prompt_sha256"])):
        actual = hashlib.sha256((run / "workspace" / filename).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Agent-visible {filename} changed after preparation")
    annotation = json.loads(Path(args.annotation).read_text())
    required = {"reviewer", "observed_resolution", "evidence_sufficient",
                "evidence", "unnecessary_question_count", "notes"}
    if set(annotation) != required:
        raise ValueError(f"Annotation fields must be exactly {sorted(required)}")
    if not isinstance(annotation["reviewer"], str) or not annotation["reviewer"].strip():
        raise ValueError("A reviewer name is required")
    if annotation["observed_resolution"] not in ("act", "explore", "experiment", "ask", "unclear"):
        raise ValueError("Unknown observed resolution")
    if type(annotation["evidence_sufficient"]) is not bool:
        raise ValueError("evidence_sufficient must be boolean")
    if not isinstance(annotation["evidence"], list) or not annotation["evidence"] or not all(isinstance(x, str) and x.strip() for x in annotation["evidence"]):
        raise ValueError("Cite at least one trace event or line")
    if not isinstance(annotation["notes"], str):
        raise ValueError("notes must be a string")
    trace = Path(args.trace).resolve()
    if not trace.is_file() or not trace.read_bytes().strip():
        raise ValueError("A nonempty full agent trace is required")
    if (run / "control" / "review.json").exists() and not args.replace:
        raise FileExistsError("Review exists; use --replace to update it")
    with redirect_stdout(io.StringIO()) as output:
        benchmark.grade(argparse.Namespace(run=str(run)))
    grade = json.loads(output.getvalue())
    questions = grade["question_count"]
    unnecessary = annotation["unnecessary_question_count"]
    if type(unnecessary) is not int or not 0 <= unnecessary <= questions:
        raise ValueError("unnecessary_question_count must be between zero and question_count")
    saved_trace = run / "control" / "agent_trace" / trace.name
    saved_trace.parent.mkdir(exist_ok=True)
    if trace != saved_trace:
        shutil.copyfile(trace, saved_trace)
    report = {
        **study,
        "run_path": str(run),
        "functional_pass": grade["functional_pass"],
        "question_count": questions,
        "provider_probe_count": grade["provider_probe_count"],
        "observed_resolution": annotation["observed_resolution"],
        "evidence_sufficient": annotation["evidence_sufficient"],
        "decision_correct": annotation["evidence_sufficient"] and annotation["observed_resolution"] in task["acceptable_resolution"],
        "unnecessary_question_count": unnecessary,
        "evidence": annotation["evidence"],
        "reviewer": annotation["reviewer"],
        "notes": annotation["notes"],
        "trace_sha256": hashlib.sha256(saved_trace.read_bytes()).hexdigest(),
        "trace_file": str(saved_trace),
        "grade_file": grade["result_file"],
    }
    write_json(run / "control" / "review.json", report)
    print(json.dumps(report, indent=2))


def summarize(args):
    root = Path(args.runs_dir).resolve()
    reports = [json.loads(path.read_text()) for path in root.glob("*/control/review.json")]
    if not reports:
        raise ValueError("No reviewed runs found")
    cells = [(r["task_id"], r["trial"], r["condition"]) for r in reports]
    if len(cells) != len(set(cells)):
        raise ValueError("Duplicate task/trial/condition runs; resolve before summarizing")
    blocks = sorted({(task, trial) for task, trial, _ in cells})
    incomplete = [{"task_id": task, "trial": trial,
                   "missing_conditions": sorted(set(CONDITIONS) - {condition for t, n, condition in cells if (t, n) == (task, trial)})}
                  for task, trial in blocks]
    incomplete = [block for block in incomplete if block["missing_conditions"]]
    rows = []
    for condition in CONDITIONS:
        subset = [r for r in reports if r["condition"] == condition]
        if not subset:
            continue
        rows.append({
            "condition": condition,
            "runs": len(subset),
            "functional_passes": sum(r["functional_pass"] for r in subset),
            "decision_correct": sum(r["decision_correct"] for r in subset),
            "questions": sum(r["question_count"] for r in subset),
            "unnecessary_questions": sum(r["unnecessary_question_count"] for r in subset),
            "provider_probes": sum(r["provider_probe_count"] for r in subset),
            "by_category": {category: {
                "runs": len(group := [r for r in subset if r["task_id"].startswith(category + "_")]),
                "functional_passes": sum(r["functional_pass"] for r in group),
                "decision_correct": sum(r["decision_correct"] for r in group),
            } for category in ("act", "explore", "experiment", "ask")},
        })
    summary = {"reviewed_runs": len(reports), "complete_blocks": len(blocks) - len(incomplete),
               "incomplete_blocks": incomplete, "conditions": rows,
               "note": "Descriptive counts only. Compare conditions only on complete task/trial blocks."}
    if args.output:
        write_json(Path(args.output), summary)
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare", help="Prepare one condition-specific run")
    p.add_argument("task")
    p.add_argument("--condition", required=True, choices=CONDITIONS)
    p.add_argument("--trial", type=int, default=1)
    p.add_argument("--run", required=True)
    p = sub.add_parser("review", help="Grade and attach a manual trace review")
    p.add_argument("--run", required=True)
    p.add_argument("--trace", required=True)
    p.add_argument("--annotation", required=True)
    p.add_argument("--replace", action="store_true")
    p = sub.add_parser("summarize", help="Summarize reviewed runs")
    p.add_argument("--runs-dir", required=True)
    p.add_argument("--output")
    args = parser.parse_args()
    try:
        {"prepare": prepare, "review": review, "summarize": summarize}[args.command](args)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        parser.exit(2, f"error: {error}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
