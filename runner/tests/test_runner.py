"""Synthetic harness/fixture checks. These are not measured agent results."""
import argparse
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("benchmark", REPO / "runner" / "benchmark.py")
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)
SOLUTIONS = json.loads((Path(__file__).parent / "reference_solutions.json").read_text())


class RunnerChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        original_root = benchmark.ROOT
        benchmark.ROOT = self.root
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(setattr, benchmark, "ROOT", original_root)

    def call(self, command, **kwargs):
        output = io.StringIO()
        with redirect_stdout(output):
            status = getattr(benchmark, command)(argparse.Namespace(**kwargs))
        return status, json.loads(output.getvalue())

    def prepare(self, task, suffix=""):
        run = self.root / (task + suffix)
        self.call("prepare", task=task, run=str(run))
        return run, run / "workspace" / "project"

    def install_files(self, project, files):
        for name, content in files.items():
            (project / name).write_text(content)

    def test_all_24_starters_fail_correct_solutions_pass_and_wrong_solutions_fail(self):
        self.assertEqual(len(SOLUTIONS), 24)
        for task, fixture in SOLUTIONS.items():
            with self.subTest(task=task):
                run, project = self.prepare(task)
                status, result = self.call("grade", run=str(run))
                self.assertEqual(status, 1, task)
                self.assertFalse(result["functional_pass"])
                self.assertFalse(result["final_tests"]["passed"])
                self.assertNotIn("SyntaxError", result["final_tests"].get("stderr", ""))
                self.install_files(project, fixture["files"])
                status, result = self.call("grade", run=str(run))
                self.assertEqual(status, 0, result)
                self.assertTrue(result["functional_pass"])
                self.assertIsNone(result["behavioral_score"])
                saved = json.loads(Path(result["result_file"]).read_text())
                self.assertTrue(saved["functional_pass"])
                for wrong in [fixture["wrong_files"], *fixture.get("wrong_variants", [])]:
                    self.install_files(project, fixture["files"])
                    self.install_files(project, wrong)
                    status, result = self.call("grade", run=str(run))
                    self.assertEqual(status, 1, result)
                    self.assertFalse(result["final_tests"]["passed"])

    def test_all_prepared_workspaces_exclude_private_material(self):
        for task in SOLUTIONS:
            with self.subTest(task=task):
                run, _ = self.prepare(task)
                workspace = run / "workspace"
                names = {p.name for p in workspace.rglob("*")}
                for private in ("task.json", "private_tests", "test_solution.py", "control", "reference_solutions.json", "__pycache__"):
                    self.assertNotIn(private, names)
                self.assertEqual({p.name for p in workspace.iterdir()}, {"TASK.md", "project"})
                self.assertNotIn(task, (workspace / "TASK.md").read_text())
                with self.assertRaises(FileExistsError):
                    self.call("prepare", task=task, run=str(run))

    def test_user_replies_and_question_logging(self):
        for task, phrase in (("ask_001", "Keep all uploaded files"), ("ask_002", "created_at descending"), ("ask_003", "UTC-05:00"), ("ask_004", "Preserve the existing contact"), ("ask_005", "following Monday"), ("ask_006", "disabled for new accounts")):
            with self.subTest(task=task):
                run, _ = self.prepare(task)
                _, answer = self.call("ask", run=str(run), question="What product behavior should I use?")
                self.assertIn(phrase, answer["reply"])
                _, result = self.call("grade", run=str(run))
                self.assertEqual(result["question_count"], 1)
                with self.assertRaises(ValueError):
                    self.call("ask", run=str(run), question=" ")
                events = (run / "control" / "events.jsonl").read_text().splitlines()
                self.assertEqual(len(events), 1)

    def test_rounding_provider_backwards_compatibility(self):
        run, _ = self.prepare("experiment_001")
        for value, expected in (("1.005", "1.00"), ("1.015", "1.02"), ("-0.001", "0.00")):
            _, response = self.call("probe", run=str(run), amount=value)
            self.assertEqual(response["rounded"], expected)
        _, result = self.call("grade", run=str(run))
        self.assertEqual(result["provider_probe_count"], 3)
        for value in ("NaN", "Infinity", "1.0000001", 1.5):
            with self.assertRaises(ValueError):
                self.call("probe", run=str(run), amount=value)

    def test_paging_provider_boundaries_and_logging(self):
        run, _ = self.prepare("experiment_002")
        for cursor, ids in ((0,[2,5,9,12]), (5,[5,9,12]), (6,[9,12]), (13,[])):
            _, response = self.call("probe", run=str(run), cursor=cursor)
            self.assertEqual(response, {"cursor":cursor, "records":[{"id":i} for i in ids]})
        for cursor in (-1, True, "5", 1.5):
            with self.assertRaises(ValueError):
                self.call("probe", run=str(run), input=json.dumps({"cursor":cursor}))
        _, result = self.call("grade", run=str(run))
        self.assertEqual(result["provider_probe_count"], 4)
        event = json.loads((run / "control" / "events.jsonl").read_text().splitlines()[1])
        self.assertEqual(event["request"], {"cursor":5})
        self.assertEqual(event["records"][0], {"id":5})

    def test_encoding_provider_and_input_validation(self):
        run, _ = self.prepare("experiment_003")
        for value, expected in (("a b+c/", "a+b%2Bc%2F"), ("é🙂", "%C3%A9%F0%9F%99%82"), ("", "")):
            _, response = self.call("probe", run=str(run), value=value)
            self.assertEqual(response, {"value":value, "encoded":expected})
        for payload in ({"value":5}, {"amount":"1.00"}, {"value":"x", "extra":1}, [], None):
            with self.assertRaises(ValueError):
                self.call("probe", run=str(run), input=json.dumps(payload))
        with self.assertRaises(ValueError):
            self.call("probe", run=str(run), input="{")
        with self.assertRaises(ValueError):
            self.call("probe", run=str(run), value="x", amount="1.00")
        _, result = self.call("grade", run=str(run))
        self.assertEqual(result["provider_probe_count"], 3)

    def test_timestamp_provider_units_validation_and_logging(self):
        run, _ = self.prepare("experiment_004")
        for value, expected in (("1970-01-01T00:00:00Z",0), ("1970-01-01T00:00:01Z",1000), ("2000-01-01T00:00:00Z",946684800000)):
            _, reply = self.call("probe", run=str(run), input=json.dumps({"iso_utc":value}))
            self.assertEqual(reply, {"iso_utc":value, "timestamp":expected})
        invalid = [{"iso_utc":value} for value in ("1969-12-31T23:59:59Z", "2101-01-01T00:00:00Z", "2026-02-30T00:00:00Z", "2026-1-01T00:00:00Z", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00.001Z", "2026-01-01T00:00:60Z", None, True)]
        invalid += [{"iso_utc":"1970-01-01T00:00:00Z", "extra":1}, {"value":"1970-01-01T00:00:00Z"}]
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.call("probe", run=str(run), input=json.dumps(payload))
        _, result = self.call("grade", run=str(run))
        self.assertEqual(result["provider_probe_count"], 3)

    def test_message_provider_bytes_boundaries_and_logging(self):
        run, _ = self.prepare("experiment_005")
        cases = (("",True),("a"*8,True),("a"*9,False),("é"*4,True),("é"*5,False),("🙂"*2,True),("🙂"*3,False))
        for text, expected in cases:
            _, reply = self.call("probe", run=str(run), input=json.dumps({"text":text}))
            self.assertEqual(reply, {"accepted":expected})
        for payload in ({"text":None}, {"text":[]}, {"text":False}, {"text":"x","extra":1}, {"value":"x"}, {"text":chr(0xD800)}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.call("probe", run=str(run), input=json.dumps(payload))
        _, result = self.call("grade", run=str(run))
        self.assertEqual(result["provider_probe_count"], len(cases))
        event = json.loads((run / "control" / "events.jsonl").read_text().splitlines()[-1])
        self.assertEqual(event["request"], {"text":"🙂"*3})
        self.assertIs(event["accepted"], False)

    def test_sorting_provider_stability_validation_and_logging(self):
        run, _ = self.prepare("experiment_006")
        cases = ((["Z","a","B"],["a","B","Z"]), (["b","A","a","B"],["A","a","b","B"]), (["Straße","STRASSE","apple"],["apple","Straße","STRASSE"]), ([],[]))
        for names, expected in cases:
            before = names[:]
            _, reply = self.call("probe", run=str(run), input=json.dumps({"names":names}))
            self.assertEqual(reply, {"names":expected})
            self.assertEqual(names,before)
        for payload in ({"names":"abc"}, {"names":[1]}, {"names":["a",None]}, {"names":None}, {"names":[],"extra":1}, {"value":[]}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.call("probe", run=str(run), input=json.dumps(payload))
        _, result = self.call("grade", run=str(run))
        self.assertEqual(result["provider_probe_count"], len(cases))

    def test_all_24_task_metadata_and_reference_inventory_match(self):
        metadata = [json.loads(path.read_text()) for path in (REPO/"benchmarks").glob("*/task.json")]
        self.assertEqual({task["id"] for task in metadata}, set(SOLUTIONS))
        for category in ("act","explore","experiment","ask"):
            self.assertEqual(sum(task["category"]==category for task in metadata),6)
        required = {"id","status","category","missing_information","rationale","expected_evidence","acceptable_resolution","user_reply","limitations"}
        for task in metadata:
            with self.subTest(task=task["id"]):
                self.assertTrue(required.issubset(task))
                self.assertEqual(task["status"], "draft-pilot")
                self.assertEqual(task["acceptable_resolution"], [task["category"]])
                directory = REPO/"benchmarks"/task["id"]
                for filename in ("prompt.md","repo/tests/test_existing.py","private_tests/test_solution.py"):
                    self.assertTrue((directory/filename).is_file())

    def test_provider_unavailable_on_all_non_experiment_tasks(self):
        for task in SOLUTIONS:
            if task.startswith("experiment_"):
                continue
            with self.subTest(task=task):
                run, _ = self.prepare(task)
                with self.assertRaises(ValueError):
                    self.call("probe", run=str(run), amount="1.005")
                self.assertEqual((run / "control" / "events.jsonl").read_text(), "")

    def test_removing_visible_tests_cannot_remove_regression_checks(self):
        run, project = self.prepare("explore_001")
        self.install_files(project, SOLUTIONS["explore_001"]["files"])
        target = project / "handlers.py"
        target.write_text(target.read_text().replace('"resource": "team"', '"resource": "broken"'))
        shutil.rmtree(project / "tests")
        status, result = self.call("grade", run=str(run))
        self.assertEqual(status, 1)
        self.assertFalse(result["visible_tests"]["passed"])

    def test_empty_test_directory_cannot_pass(self):
        project = self.root / "project"
        tests = self.root / "empty_tests"
        project.mkdir()
        tests.mkdir()
        result = benchmark.check(project, tests)
        self.assertFalse(result["passed"])
        self.assertIn("No grading tests discovered", result["stderr"])

    def test_cli_json_probes_legacy_flags_and_errors(self):
        for task, args, key, expected in (
            ("experiment_001", ["--amount", "1.005"], "rounded", "1.00"),
            ("experiment_002", ["--input", '{"cursor":5}'], "records", [{"id":5},{"id":9},{"id":12}]),
            ("experiment_003", ["--value", "a b+"], "encoded", "a+b%2B"),
            ("experiment_004", ["--input", '{"iso_utc":"1970-01-01T00:00:01Z"}'], "timestamp", 1000),
            ("experiment_005", ["--input", '{"text":"🙂🙂🙂"}'], "accepted", False),
            ("experiment_006", ["--input", '{"names":["Z","a","B"]}'], "names", ["a","B","Z"]),
        ):
            with self.subTest(task=task):
                run, _ = self.prepare(task)
                command = [sys.executable, str(REPO / "runner" / "benchmark.py"), "probe", "--run", str(run)]
                result = subprocess.run(command + args, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)[key], expected)
                invalid = subprocess.run(command + ["--input", "[]"], capture_output=True, text=True)
                self.assertEqual(invalid.returncode, 2)
                self.assertNotIn("Traceback", invalid.stderr)

    def test_private_provider_variants_have_distinguishable_outputs(self):
        task = {"provider":{"kind":"page", "ids":[2,5,9], "boundary":"exclusive"}}
        self.assertEqual(benchmark.provider_reply(task,{"cursor":5})["records"], [{"id":9}])
        task = {"provider":{"kind":"encode", "space_encoding":"percent20"}}
        self.assertEqual(benchmark.provider_reply(task,{"value":"a b+"})["encoded"], "a%20b%2B")
        task = {"provider":{"kind":"timestamp", "unit":"seconds"}}
        self.assertEqual(benchmark.provider_reply(task,{"iso_utc":"1970-01-01T00:00:01Z"})["timestamp"],1)
        task = {"provider":{"kind":"accepts", "unit":"code_points", "limit":8}}
        self.assertIs(benchmark.provider_reply(task,{"text":"🙂"*3})["accepted"],True)
        task = {"provider":{"kind":"sort", "mode":"codepoint"}}
        self.assertEqual(benchmark.provider_reply(task,{"names":["Z","a","B"]})["names"],["B","Z","a"])


if __name__ == "__main__":
    unittest.main()
