"""Boundary checks for the containerized Claude Code adapter (no Docker needed)."""

import argparse
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import urllib.error
import urllib.request

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "runner"))
import benchmark  # noqa: E402
import claude_agent  # noqa: E402
import study  # noqa: E402


class ClaudeAgentChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.server = claude_agent.start_tool_server()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def prepare(self, task_id):
        run = self.root / task_id
        with redirect_stdout(io.StringIO()):
            study.prepare(argparse.Namespace(task=task_id, condition="standard", trial=1, run=str(run)))
        self.server.runs[task_id] = (run, benchmark.task_data(task_id)[1])
        return run

    def post(self, token, method, params=None, request_id=1):
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        if request_id is not None:
            body["id"] = request_id
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.server.server_address[1]}/mcp/{token}",
            data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=5) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None

    def call(self, token, name, arguments):
        result = self.post(token, "tools/call", {"name": name, "arguments": arguments})[1]["result"]
        return result["isError"], json.loads(result["content"][0]["text"])

    def test_tool_server_speaks_mcp_and_logs_calls(self):
        run = self.prepare("ask_001")
        status, reply = self.post("ask_001", "initialize", {"protocolVersion": "2025-06-18"})
        self.assertEqual((status, reply["result"]["protocolVersion"]), (200, "2025-06-18"))
        self.assertEqual(self.post("ask_001", "notifications/initialized", request_id=None), (202, None))
        tools = self.post("ask_001", "tools/list")[1]["result"]["tools"]
        self.assertEqual([tool["name"] for tool in tools], ["ask_user", "probe_provider"])
        failed, reply = self.call("ask_001", "ask_user", {"question": "Keep the uploads?"})
        self.assertFalse(failed)
        self.assertIn("Keep all uploaded files", reply["reply"])
        events = (run / "control" / "events.jsonl").read_text().splitlines()
        self.assertEqual(json.loads(events[0])["question"], "Keep the uploads?")
        # No provider on an ask task; errors are returned, not logged.
        failed, reply = self.call("ask_001", "probe_provider", {"payload": {"amount": "1.005"}})
        self.assertTrue(failed)
        self.assertEqual(len((run / "control" / "events.jsonl").read_text().splitlines()), 1)

    def test_probe_reaches_only_the_run_named_by_the_token(self):
        run = self.prepare("experiment_002")
        failed, reply = self.call("experiment_002", "probe_provider", {"payload": {"cursor": 5}})
        self.assertFalse(failed)
        self.assertEqual([r["id"] for r in reply["records"]], [5, 9, 12])
        self.assertEqual(len((run / "control" / "events.jsonl").read_text().splitlines()), 1)
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.post("wrong-token", "tools/list")
        self.assertEqual(caught.exception.code, 404)

    def test_container_gets_only_the_workspace_and_no_secret_values(self):
        args = argparse.Namespace(image="img", model="m")
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "secret-value"}):
            command = claude_agent.docker_command(args, "name", Path("/runs/x/workspace"), "prompt", "http://h/mcp/t")
        self.assertEqual([command[i + 1] for i, part in enumerate(command) if part == "-v"],
                         ["/runs/x/workspace:/workspace"])
        self.assertNotIn("secret-value", " ".join(command))
        self.assertEqual(command[command.index("--tools") + 1], "Bash,Read,Edit,Write,Glob,Grep")
        self.assertIn("--strict-mcp-config", command)

    def test_stream_is_normalized_to_adapter_trace_events(self):
        def assistant(*blocks):
            return json.dumps({"type": "assistant", "message": {"content": list(blocks)}})

        def use(tool_id, name, tool_input):
            return {"type": "tool_use", "id": tool_id, "name": name, "input": tool_input}

        def result(tool_id, text, is_error=False):
            return json.dumps({"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": tool_id, "content": [{"type": "text", "text": text}],
                 "is_error": is_error}]}})

        lines = [
            json.dumps({"type": "system", "subtype": "init", "model": "claude-x", "claude_code_version": "9"}),
            "not json",
            assistant(use("a", "Read", {"file_path": "/workspace/project/projects.py"})),
            result("a", "def delete_project"),
            assistant(use("b", "mcp__bench__ask_user", {"question": "Keep uploads?"})),
            result("b", '{"reply": "Keep"}'),
            assistant(use("c", "Bash", {"command": "curl https://example.com"})),
            result("c", "denied", is_error=True),
            assistant(use("d", "Edit", {"file_path": "/workspace/project/projects.py", "old_string": "a", "new_string": "b"})),
            result("d", "updated"),
            json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "Done", "num_turns": 5}),
        ]
        events, status, error, facts = claude_agent.normalize(lines)
        tools = [event for event in events if event["type"] == "tool"]
        self.assertEqual([(t["name"], t["arguments"].get("path")) for t in tools],
                         [("read_file", "project/projects.py"), ("ask_user", None), ("bash", None),
                          ("write_file", "project/projects.py")])
        self.assertEqual(tools[1]["result"], {"reply": "Keep"})
        self.assertIn("error", tools[2]["result"])
        self.assertEqual((status, error, facts["model"], facts["num_turns"]), ("finished", None, "claude-x", 5))
        self.assertEqual(claude_agent.network_commands(events), ["curl https://example.com"])
        self.assertEqual(claude_agent.normalize(lines[:-1])[1], "error")
        failed = json.dumps({"type": "result", "subtype": "success", "is_error": True, "result": "Invalid API key"})
        self.assertEqual(claude_agent.normalize([failed])[1:3], ("error", "Invalid API key"))

    def test_shell_reads_and_writes_become_file_events(self):
        run = self.prepare("explore_001")
        files = claude_agent.workspace_files(run / "workspace")
        self.assertEqual(files["handlers.py"], "project/handlers.py")
        module, tests = "project/handlers.py", "project/tests/test_existing.py"
        cases = {
            "cd /workspace/project; cat handlers.py; ls": [("read_file", module)],
            "sed -n '1,9p' /workspace/project/handlers.py": [("read_file", module)],
            "cat tests/test_existing.py && cat TASK.md | head -5": [("read_file", tests), ("read_file", "TASK.md")],
            "cat handlers.py > /tmp/copy.py": [("read_file", module)],
            "sed -i 's/a/b/' handlers.py; python -m unittest 2>&1 | tail -4": [("write_file", module)],
            "echo x >> ./handlers.py": [("write_file", module)],
            # File content inside the heredoc is not a command, even if it names other files.
            "cat > handlers.py <<'E'\nopen('TASK.md')\nE\npython -m unittest": [("write_file", module)],
            "python - <<'E'\ns=open('handlers.py').read()\nopen('handlers.py','w').write(s)\nE": [("write_file", module)],
            "python - <<'E'\nprint(open('handlers.py').read())\nE": [("read_file", module)],
            "python -m unittest discover -s tests": [],
            "cat my_handlers.py other.py": [],
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                self.assertEqual(claude_agent.shell_file_events(command, files), expected)
        stream = [
            json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": "a", "name": "Bash", "input": {"command": "cat handlers.py; echo x >> handlers.py"}}]}}),
            json.dumps({"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "a", "content": "ok"}]}}),
        ]
        tools = [event for event in claude_agent.normalize(stream, files)[0] if event["type"] == "tool"]
        self.assertEqual([(t["name"], t["arguments"].get("path")) for t in tools],
                         [("bash", None), ("read_file", module), ("write_file", module)])
        self.assertEqual(tools[2]["result"], {"derived_from": "bash"})


if __name__ == "__main__":
    unittest.main()
