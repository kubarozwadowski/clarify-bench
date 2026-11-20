#!/usr/bin/env python3
"""Compute narrow, auditable source-evidence metrics from local-agent traces.

These rules check observable actions, not the agent's intent or the necessity
of every question. They supplement, rather than replace, manual trace review.
"""

import argparse
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP
import json
from pathlib import Path
import re

import benchmark
import study


ASK_TERMS = {
    "ask_001": r"upload|file",
    "ask_002": r"order|sort",
    "ask_003": r"time.?zone|offset",
    "ask_004": r"duplicate|existing|already exist|overwrite|same email",
    "ask_005": r"weekend|saturday|sunday",
    "ask_006": r"notification",
}


def decisive_probe(task_id, payload, task):
    try:
        if task_id == "experiment_001":
            amount = Decimal(payload["amount"])
            cent = Decimal("0.01")
            return amount.quantize(cent, rounding=ROUND_HALF_EVEN) != amount.quantize(cent, rounding=ROUND_HALF_UP)
        if task_id == "experiment_002":
            return payload["cursor"] in task["provider"]["ids"]
        if task_id == "experiment_003":
            return " " in payload["value"]
        if task_id == "experiment_004":
            return payload["iso_utc"] != "1970-01-01T00:00:00Z"
        if task_id == "experiment_005":
            text = payload["text"]
            limit = task["provider"]["limit"]
            return len(text) <= limit < len(text.encode("utf-8"))
        if task_id == "experiment_006":
            names = payload["names"]
            return sorted(names) != sorted(names, key=str.casefold)
    except (KeyError, TypeError, ValueError, ArithmeticError):
        return False
    return False


def one_run(result, group=None):
    task_id = result["task_id"]
    category = result["category"]
    task = benchmark.task_data(task_id)[1]
    trace = Path(result["trace_file"])
    if not trace.is_file() and group is not None:
        trace = Path(group) / Path(result["run_path"]).name / "control" / "agent_trace.jsonl"
    events = [json.loads(line) for line in trace.read_text().splitlines() if line.strip()]
    tools = [(index + 1, event) for index, event in enumerate(events) if event.get("type") == "tool"]
    writes = [(line, event) for line, event in tools if event["name"] == "write_file" and "error" not in event.get("result", {})]
    first_write = writes[0][0] if writes else float("inf")
    earlier = [(line, event) for line, event in tools if line < first_write]
    asks = [(line, event) for line, event in earlier if event["name"] == "ask_user" and "error" not in event.get("result", {})]
    probes = [(line, event) for line, event in earlier if event["name"] == "probe_provider" and "error" not in event.get("result", {})]
    citations = []
    if category == "act":
        extra = [event for _, event in tools if event["name"] in ("ask_user", "probe_provider") and "error" not in event.get("result", {})]
        evidence = bool(writes) and not extra
        if evidence:
            citations = [f"trace line {writes[0][0]}: direct edit"]
    elif category == "explore":
        target = writes[0][1]["arguments"].get("path") if writes else None
        matching = [(line, event) for line, event in earlier if event["name"] == "read_file" and event["arguments"].get("path") == target]
        evidence = bool(matching)
        if evidence:
            citations = [f"trace line {matching[0][0]}: read existing module before edit"]
    elif category == "experiment":
        matching = [(line, event) for line, event in probes if decisive_probe(task_id, event["arguments"].get("payload", {}), task)]
        evidence = bool(matching)
        if evidence:
            citations = [f"trace line {matching[0][0]}: discriminating provider probe"]
    else:
        matching = [(line, event) for line, event in asks if re.search(ASK_TERMS[task_id], event["arguments"].get("question", ""), re.I)]
        evidence = bool(matching)
        if evidence:
            citations = [f"trace line {matching[0][0]}: targeted product question before edit"]
    return {"task_id": task_id, "category": category, "condition": result["condition"],
            "trial": result["trial"], "functional_pass": result["functional_pass"],
            "source_evidence": evidence, "functional_with_evidence": bool(result["functional_pass"] and evidence),
            "evidence": citations, "question_count": result["question_count"],
            "provider_probe_count": result["provider_probe_count"],
            "non_ask_question_count": result["question_count"] if category != "ask" else 0,
            "trace_file": str(trace)}


def summarize(group):
    group = Path(group)
    raw = json.loads((group / "agent_results.json").read_text())
    rows = [one_run(result, group) for result in raw]
    def counts(subset):
        return {"runs": len(subset), "functional_passes": sum(r["functional_pass"] for r in subset),
                "source_evidence": sum(r["source_evidence"] for r in subset),
                "functional_with_evidence": sum(r["functional_with_evidence"] for r in subset),
                "questions": sum(r["question_count"] for r in subset),
                "questions_on_non_ask_tasks": sum(r["non_ask_question_count"] for r in subset),
                "provider_probes": sum(r["provider_probe_count"] for r in subset)}
    return {"overall": counts(rows), "conditions": {
        condition: {**counts(subset := [r for r in rows if r["condition"] == condition]),
                    "by_category": {category: counts([r for r in subset if r["category"] == category])
                                    for category in ("act", "explore", "experiment", "ask")}}
        for condition in study.CONDITIONS}, "runs": rows,
        "note": "Source-evidence rules are task-specific trace checks, not manual decision-accuracy or unnecessary-question judgments."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group")
    parser.add_argument("--output")
    args = parser.parse_args()
    summary = summarize(args.group)
    output = Path(args.output) if args.output else Path(args.group) / "trace_metrics.json"
    output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"overall": summary["overall"], "conditions": summary["conditions"]}, indent=2))


if __name__ == "__main__":
    main()
