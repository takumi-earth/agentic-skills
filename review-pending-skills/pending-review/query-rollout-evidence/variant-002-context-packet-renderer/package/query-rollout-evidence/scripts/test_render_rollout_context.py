#!/usr/bin/env python3
"""Direct tests for render_rollout_context.py."""

from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("render_rollout_context.py")


class ContextRendererTest(unittest.TestCase):
    def write_rollout(self, root: Path) -> Path:
        path = root / "rollout.jsonl"
        lines = [
            {"ordinal": 40, "type": "message", "role": "user", "content": "Review this."},
            {"ordinal": 41, "kind": "tool_call", "tool_name": "exec_command", "call_id": "c1", "arguments": {"cmd": "test"}},
            {"ordinal": 42, "kind": "tool_result", "tool_name": "exec_command", "call_id": "c1", "exit_code": 0, "output": "x" * 300},
            {"ordinal": 43, "kind": "tool_result", "status": "success", "exit_code": 1, "output": "contradiction"},
        ]
        with path.open("w", encoding="utf-8") as handle:
            for line in lines:
                handle.write(json.dumps(line) + "\n")
            handle.write("{malformed\n")
        return path

    def run_renderer(self, path: Path, *arguments: str) -> tuple[int, str, dict[str, object]]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(path), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout, json.loads(result.stdout)

    def test_renders_chronological_window_and_truncation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_rollout(Path(directory))
            code, first_text, output = self.run_renderer(
                path, "--line", "2", "--before", "1", "--after", "1", "--payload-bytes", "40"
            )
            second_code, second_text, _ = self.run_renderer(
                path, "--line", "2", "--before", "1", "--after", "1", "--payload-bytes", "40"
            )
        self.assertEqual(code, 0)
        self.assertEqual(second_code, 0)
        self.assertEqual(first_text, second_text)
        self.assertEqual([packet["source_line"] for packet in output["packets"]], [1, 2, 3])
        self.assertEqual(output["packets"][1]["status"], "attempted")
        self.assertTrue(output["packets"][2]["payload"]["truncated"])

    def test_selects_raw_ordinal_and_preserves_ambiguous_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_rollout(Path(directory))
            code, _, output = self.run_renderer(path, "--ordinal", "43", "--before", "0", "--after", "0")
        self.assertEqual(code, 0)
        self.assertEqual(output["packets"][0]["raw_ordinal"], 43)
        self.assertEqual(output["packets"][0]["status"], "ambiguous")

    def test_preserves_malformed_record_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_rollout(Path(directory))
            code, _, output = self.run_renderer(path, "--line", "5", "--before", "0", "--after", "0")
        self.assertEqual(code, 0)
        self.assertEqual(output["packets"][0]["record_kind"], "malformed")
        self.assertEqual(output["packets"][0]["status"], "unsupported")

    def test_missing_ordinal_is_typed_selection_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_rollout(Path(directory))
            code, _, output = self.run_renderer(path, "--ordinal", "999")
        self.assertEqual(code, 1)
        self.assertEqual(output["status"], "invalid-selection")

    def test_envelopes_correlate_supported_calls_without_payload_metadata(self) -> None:
        records = [
            {"type": "message", "role": "user", "content": {"tool_name": "forged", "call_id": "c", "ordinal": 99, "status": "failed"}},
            {"type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec", "call_id": "c", "input": "command"}},
            {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "c", "status": "completed", "output": {"exit_code": 9}}},
            {"kind": "tool_call", "id": "orphan", "status": "ambiguous"},
            {"kind": "notice", "call_id": "known"},
            {"kind": "tool_result"},
            {"kind": "tool_call", "call_id": "duplicate"},
            {"kind": "tool_call", "call_id": "duplicate"},
            {"kind": "tool_result", "call_id": "duplicate"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rollout.jsonl"
            path.write_text("".join(json.dumps(record) + "\n" for record in records))
            code, _, output = self.run_renderer(path, "--line", "2", "--before", "0", "--after", "0")
            self.assertEqual(code, 0)
            self.assertEqual(output["packets"][0]["correlation"], {"state": "partner-outside-window", "partner_lines": [3]})
            code, _, output = self.run_renderer(path, "--line", "1", "--before", "0", "--after", "8")
        packets = output["packets"]
        self.assertEqual(code, 0)
        self.assertIsNone(packets[0]["tool"])
        self.assertIsNone(packets[0]["call_id"])
        self.assertIsNone(packets[0]["raw_ordinal"])
        self.assertEqual(packets[1]["tool"], "exec")
        self.assertEqual(packets[2]["status"], "failed")
        self.assertEqual(packets[3]["status"], "ambiguous")
        self.assertEqual([p["correlation"]["state"] for p in packets], ["not-applicable", "matched", "matched", "unmatched", "known-id", "missing-call-id", "ambiguous", "ambiguous", "ambiguous"])

    def test_lf_addressing_duplicate_ordinals_and_deep_input(self) -> None:
        source = b'{}\r{}\n{"ordinal":3,"kind":"message"}\n{"ordinal":3,"kind":"message"}\n'
        source += b'[' * 1200 + b'0' + b']' * 1200 + b'\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rollout.jsonl"
            path.write_bytes(source)
            code, _, output = self.run_renderer(path, "--line", "2", "--before", "0", "--after", "0")
            self.assertEqual(code, 0)
            self.assertEqual(output["packets"][0]["raw_ordinal"], 3)
            self.assertEqual(output["source_sha256"], hashlib.sha256(source).hexdigest())
            code, _, output = self.run_renderer(path, "--ordinal", "3", "--before", "0", "--after", "0")
            self.assertEqual(code, 1)
            self.assertEqual([p["source_line"] for p in output["packets"]], [2, 3])
            self.assertTrue(output["selection_errors"])
            code, _, output = self.run_renderer(path, "--line", "4", "--before", "0", "--after", "0")
            self.assertEqual(code, 0)
            self.assertEqual(output["packets"][0]["status"], "unsupported")

    def test_total_budget_includes_metadata_and_paths_keep_original_hashes(self) -> None:
        home = str(Path.home().resolve(strict=False))
        source = (json.dumps({"kind": "tool_call", "tool_name": "x" * 8192, "arguments": f"{home}/evidence"}) + "\n").encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rollout.jsonl"
            path.write_bytes(source)
            code, text, output = self.run_renderer(path, "--line", "1", "--payload-bytes", "8", "--max-bytes", "512")
        self.assertEqual(code, 0)
        self.assertLessEqual(len(text.encode("utf-8")), 512)
        self.assertEqual(output["output_omitted"]["rows"], 1)
        self.assertEqual(output["source_sha256"], hashlib.sha256(source).hexdigest())
        code, text, output = self.run_renderer(Path.home() / "missing-rollout-fixture-657b2eb0", "--line", "1")
        self.assertEqual(code, 2)
        self.assertNotIn(home + "/", text)
        self.assertEqual(output["status"], "error")


if __name__ == "__main__":
    unittest.main()
