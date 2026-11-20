#!/usr/bin/env python3
"""Summarize raw local-agent results without inventing decision scores."""

import argparse
import json
from pathlib import Path


CATEGORIES = ("act", "explore", "experiment", "ask")
CONDITIONS = ("standard", "ask_when_unsure", "decision_policy")


def summarize(group):
    group = Path(group)
    manifest = json.loads((group / "manifest.json").read_text())
    results = json.loads((group / "agent_results.json").read_text())
    expected = [tuple(item) for item in manifest["runs"]]
    observed = [(item["task_id"], item["condition"], item["trial"]) for item in results]
    if len(observed) != len(set(observed)):
        raise ValueError("Duplicate run identity in results")
    if any(item not in expected for item in observed):
        raise ValueError("Results contain runs outside the manifest")
    def counts(subset):
        return {"runs": len(subset), "functional_passes": sum(bool(r["functional_pass"]) for r in subset),
                "agent_finished": sum(r["status"] == "finished" for r in subset),
                "finished_and_passed": sum(r["status"] == "finished" and bool(r["functional_pass"]) for r in subset),
                "questions": sum(r["question_count"] for r in subset),
                "provider_probes": sum(r["provider_probe_count"] for r in subset),
                "agent_errors": sum(r["status"] == "error" for r in subset),
                "step_limits": sum(r["status"] == "step_limit" for r in subset)}
    summary = {
        "model": manifest["model"], "seed": manifest["seed"],
        "complete": len(observed) == len(expected) and set(observed) == set(expected),
        "planned_runs": len(expected), "completed_runs": len(results),
        "overall": counts(results),
        "conditions": {condition: {**counts(subset := [r for r in results if r["condition"] == condition]),
                                   "by_category": {category: counts([r for r in subset if r["category"] == category])
                                                   for category in CATEGORIES}}
                       for condition in CONDITIONS},
        "note": "Functional and tool-use counts only. Decision accuracy and unnecessary questions require trace review.",
    }
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        summary = summarize(args.group)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        parser.exit(2, f"error: {error}\n")
    output = Path(args.output) if args.output else Path(args.group) / "functional_summary.json"
    output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
