"""Check task-specific diagnostic probes and evidence boundaries."""

from pathlib import Path
import sys
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "runner"))
import benchmark  # noqa: E402
import trace_metrics  # noqa: E402


class TraceMetricChecks(unittest.TestCase):
    def test_discriminating_provider_inputs(self):
        cases = [
            ("experiment_001", {"amount":"1.005"}, {"amount":"1.015"}),
            ("experiment_002", {"cursor":5}, {"cursor":6}),
            ("experiment_003", {"value":"a b"}, {"value":"ab"}),
            ("experiment_004", {"iso_utc":"1970-01-01T00:00:01Z"}, {"iso_utc":"1970-01-01T00:00:00Z"}),
            ("experiment_005", {"text":"🙂🙂🙂"}, {"text":"abcdefgh"}),
            ("experiment_006", {"names":["Z","a"]}, {"names":["a","b"]}),
        ]
        for task_id, decisive, ambiguous in cases:
            with self.subTest(task_id=task_id):
                task = benchmark.task_data(task_id)[1]
                self.assertTrue(trace_metrics.decisive_probe(task_id, decisive, task))
                self.assertFalse(trace_metrics.decisive_probe(task_id, ambiguous, task))


if __name__ == "__main__":
    unittest.main()
