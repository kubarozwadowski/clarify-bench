"""Harness checks using synthetic completed solutions; these are not agent results."""
import argparse
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("benchmark", REPO / "runner" / "benchmark.py")
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


class RunnerChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.original_root = benchmark.ROOT
        benchmark.ROOT = self.root  # Keep test-generated result files out of the repository.
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(setattr, benchmark, "ROOT", self.original_root)

    def call(self, command, **kwargs):
        output = io.StringIO()
        with redirect_stdout(output):
            status = getattr(benchmark, command)(argparse.Namespace(**kwargs))
        return status, json.loads(output.getvalue())

    def prepare(self, task):
        run = self.root / task
        self.call("prepare", task=task, run=str(run))
        return run, run / "workspace" / "project"

    def test_starters_fail_and_completed_solutions_pass(self):
        for task in ("act_001", "explore_001", "experiment_001", "ask_001"):
            with self.subTest(task=task):
                run, project = self.prepare(task)
                status, result = self.call("grade", run=str(run))
                self.assertEqual(status, 1)
                self.assertFalse(result["functional_pass"])
                if task == "act_001":
                    target = project / "pagination.py"
                    target.write_text(target.read_text().replace("page_size=10", "page_size=20"))
                elif task == "explore_001":
                    target = project / "handlers.py"
                    target.write_text(target.read_text().replace(
                        'raise NotImplementedError("Add the project lookup handler")',
                        'if project_id not in projects:\n'
                        '        return 404, {"error": {"code": "not_found", "resource": "project", "id": project_id}}\n'
                        '    return 200, {"data": projects[project_id]}'
                    ))
                elif task == "experiment_001":
                    (project / "pricing.py").write_text(
                        'from decimal import Decimal, ROUND_HALF_EVEN\n'
                        'def round_price(amount):\n'
                        '    value = Decimal(amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)\n'
                        '    return format(abs(value) if value == 0 else value, ".2f")\n'
                    )
                else:
                    (project / "projects.py").write_text(
                        'def delete_project(state, project_id):\n'
                        '    if project_id not in state["projects"]:\n'
                        '        return False\n'
                        '    del state["projects"][project_id]\n'
                        '    return True\n'
                    )
                status, result = self.call("grade", run=str(run))
                self.assertEqual(status, 0, result)
                self.assertTrue(result["functional_pass"])
                self.assertIsNone(result["behavioral_score"])

    def test_prepared_workspace_excludes_private_material(self):
        run, _ = self.prepare("ask_001")
        files = {path.name for path in (run / "workspace").rglob("*")}
        self.assertNotIn("task.json", files)
        self.assertNotIn("private_tests", files)
        self.assertNotIn("test_solution.py", files)
        self.assertNotIn("control", files)
        prompt = (run / "workspace" / "TASK.md").read_text()
        self.assertNotIn("ask_001", prompt)
        with self.assertRaises(FileExistsError):
            self.call("prepare", task="ask_001", run=str(run))

    def test_user_reply_and_question_logging(self):
        run, _ = self.prepare("ask_001")
        _, answer = self.call("ask", run=str(run), question="Keep or remove associated uploads?")
        self.assertIn("Keep all uploaded files", answer["reply"])
        _, result = self.call("grade", run=str(run))
        self.assertEqual(result["question_count"], 1)
        with self.assertRaises(ValueError):
            self.call("ask", run=str(run), question=" ")

    def test_provider_probes_and_availability(self):
        run, _ = self.prepare("experiment_001")
        for value, expected in (("1.005", "1.00"), ("1.015", "1.02"), ("-0.001", "0.00")):
            _, response = self.call("probe", run=str(run), amount=value)
            self.assertEqual(response["rounded"], expected)
        _, result = self.call("grade", run=str(run))
        self.assertEqual(result["provider_probe_count"], 3)
        for value in ("NaN", "Infinity", "1.0000001"):
            with self.assertRaises(ValueError):
                self.call("probe", run=str(run), amount=value)
        other_run, _ = self.prepare("act_001")
        with self.assertRaises(ValueError):
            self.call("probe", run=str(other_run), amount="1.005")


if __name__ == "__main__":
    unittest.main()
