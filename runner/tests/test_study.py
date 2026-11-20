"""Checks for the researcher-side study workflow, not agent results."""

import argparse
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "runner"))
import benchmark  # noqa: E402
import study  # noqa: E402


class StudyChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        previous = benchmark.ROOT
        benchmark.ROOT = self.root
        self.addCleanup(setattr, benchmark, "ROOT", previous)

    def call(self, function, **kwargs):
        output = io.StringIO()
        with redirect_stdout(output):
            function(argparse.Namespace(**kwargs))
        return json.loads(output.getvalue())

    def test_prepare_has_equal_task_prompt_and_distinct_condition_instructions(self):
        prompts = set()
        instructions = set()
        for condition in study.CONDITIONS:
            run = self.root / condition
            self.call(study.prepare, task="act_001", condition=condition, trial=1, run=str(run))
            workspace = run / "workspace"
            prompts.add((workspace / "TASK.md").read_text())
            instructions.add((workspace / "AGENT_INSTRUCTIONS.md").read_text())
            self.assertEqual({p.name for p in workspace.iterdir()}, {"TASK.md", "AGENT_INSTRUCTIONS.md", "project"})
            self.assertNotIn("act_001", (workspace / "AGENT_INSTRUCTIONS.md").read_text())
        self.assertEqual(len(prompts), 1)
        self.assertEqual(len(instructions), 3)

    def test_review_requires_trace_and_counts_questions_separately(self):
        run = self.root / "pilot"
        self.call(study.prepare, task="act_001", condition="standard", trial=1, run=str(run))
        solution = json.loads((REPO / "runner" / "tests" / "reference_solutions.json").read_text())["act_001"]["files"]["pagination.py"]
        (run / "workspace" / "project" / "pagination.py").write_text(solution)
        with redirect_stdout(io.StringIO()):
            benchmark.ask(argparse.Namespace(run=str(run), question="Is the default really 20?"))
        annotation = self.root / "annotation.json"
        annotation.write_text(json.dumps({"reviewer":"Reviewer 1", "observed_resolution":"act",
                                          "evidence_sufficient":True, "evidence":["trace line 1: request read"],
                                          "unnecessary_question_count":1, "notes":"Prompt already specifies 20."}))
        trace = self.root / "trace.jsonl"
        with self.assertRaises(ValueError):
            self.call(study.review, run=str(run), trace=str(trace), annotation=str(annotation), replace=False)
        trace.write_text('{"event":"read TASK.md"}\n')
        report = self.call(study.review, run=str(run), trace=str(trace), annotation=str(annotation), replace=False)
        self.assertTrue(report["functional_pass"])
        self.assertTrue(report["decision_correct"])
        self.assertEqual(report["question_count"], 1)
        self.assertEqual(report["unnecessary_question_count"], 1)
        self.assertTrue(Path(report["trace_file"]).is_file())
        with self.assertRaises(FileExistsError):
            self.call(study.review, run=str(run), trace=str(trace), annotation=str(annotation), replace=False)

    def test_summary_flags_incomplete_condition_blocks(self):
        run = self.root / "pilot"
        self.call(study.prepare, task="act_001", condition="standard", trial=1, run=str(run))
        review = {"task_id":"act_001", "trial":1, "condition":"standard", "functional_pass":False,
                  "decision_correct":True, "question_count":0, "unnecessary_question_count":0,
                  "provider_probe_count":0}
        study.write_json(run / "control" / "review.json", review)
        summary = self.call(study.summarize, runs_dir=str(self.root), output=None)
        self.assertEqual(summary["reviewed_runs"], 1)
        self.assertEqual(summary["complete_blocks"], 0)
        self.assertEqual(summary["incomplete_blocks"][0]["missing_conditions"],
                         ["ask_when_unsure", "decision_policy"])

    def test_review_rejects_changed_task_prompt(self):
        run = self.root / "pilot"
        self.call(study.prepare, task="act_001", condition="standard", trial=1, run=str(run))
        (run / "workspace" / "TASK.md").write_text("Changed request")
        trace = self.root / "trace.jsonl"
        trace.write_text('{"event":"read TASK.md"}\n')
        annotation = self.root / "annotation.json"
        annotation.write_text(json.dumps({"reviewer":"Reviewer 1", "observed_resolution":"act",
                                          "evidence_sufficient":True, "evidence":["trace line 1"],
                                          "unnecessary_question_count":0, "notes":""}))
        with self.assertRaisesRegex(ValueError, "TASK.md changed"):
            self.call(study.review, run=str(run), trace=str(trace), annotation=str(annotation), replace=False)


if __name__ == "__main__":
    unittest.main()
