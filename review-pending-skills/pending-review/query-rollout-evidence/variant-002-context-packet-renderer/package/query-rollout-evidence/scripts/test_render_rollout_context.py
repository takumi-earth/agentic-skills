#!/usr/bin/env python3
"""Direct tests for render_rollout_context.py."""

from __future__ import annotations

import json
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


if __name__ == "__main__":
    unittest.main()
