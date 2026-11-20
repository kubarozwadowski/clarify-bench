"""Check complete-run accounting for raw study reports."""

import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "runner"))
import report  # noqa: E402


class ReportChecks(unittest.TestCase):
    def test_incomplete_manifest_is_explicit(self):
        with tempfile.TemporaryDirectory() as folder:
            group = Path(folder)
            (group / "manifest.json").write_text(json.dumps({"model":"local", "seed":1,
                "runs":[["act_001","standard",1],["act_001","decision_policy",1]]}))
            (group / "agent_results.json").write_text(json.dumps([{
                "task_id":"act_001", "condition":"standard", "trial":1, "category":"act",
                "functional_pass":True, "question_count":0, "provider_probe_count":0,
                "status":"finished"}]))
            result = report.summarize(group)
            self.assertFalse(result["complete"])
            self.assertEqual(result["planned_runs"], 2)
            self.assertEqual(result["completed_runs"], 1)
            self.assertEqual(result["conditions"]["standard"]["functional_passes"], 1)
            self.assertEqual(result["conditions"]["decision_policy"]["runs"], 0)


if __name__ == "__main__":
    unittest.main()
