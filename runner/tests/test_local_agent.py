"""Boundary checks for the local-model pilot adapter."""

import argparse
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "runner"))
import benchmark  # noqa: E402
import local_agent  # noqa: E402
import study  # noqa: E402


class LocalAgentChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        previous = benchmark.ROOT
        benchmark.ROOT = self.root
        self.addCleanup(setattr, benchmark, "ROOT", previous)

    def prepare(self, task_id):
        run = self.root / task_id
        with redirect_stdout(io.StringIO()):
            study.prepare(argparse.Namespace(task=task_id, condition="standard", trial=1, run=str(run)))
        return run, benchmark.task_data(task_id)[1]

    def test_file_tools_only_expose_workspace_and_edit_module(self):
        run, task = self.prepare("act_001")
        files = local_agent.use_tool("list_files", {}, run, task)["files"]
        self.assertIn("project/pagination.py", files)
        self.assertNotIn("task.json", files)
        original = local_agent.use_tool("read_file", {"path":"project/pagination.py"}, run, task)["content"]
        self.assertIn("page_size=10", original)
        for path in ("../task.json", "/etc/hosts", "project/tests/test_existing.py", "TASK.md"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                local_agent.use_tool("write_file", {"path":path, "content":"changed"}, run, task)
        local_agent.use_tool("write_file", {"path":"project/pagination.py", "content":original.replace("page_size=10", "page_size=20")}, run, task)
        self.assertTrue(local_agent.use_tool("run_tests", {}, run, task)["passed"])

    def test_provider_reply_is_logged_without_exposing_private_source(self):
        run, task = self.prepare("experiment_002")
        reply = local_agent.use_tool("probe_provider", {"payload":{"cursor":5}}, run, task)
        self.assertEqual([r["id"] for r in reply["records"]], [5, 9, 12])
        self.assertEqual(len((run / "control" / "events.jsonl").read_text().splitlines()), 1)
        with self.assertRaises(ValueError):
            local_agent.use_tool("read_file", {"path":"../task.json"}, run, task)


if __name__ == "__main__":
    unittest.main()
