#!/usr/bin/env python3
"""Direct tests for query_rollout_index.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("query_rollout_index.py")


class RolloutQueryTest(unittest.TestCase):
    def write_index(self, root: Path) -> Path:
        path = root / "index.jsonl"
        records = [
            {"ordinal": 10, "kind": "tool_call", "tool_name": "exec_command", "call_id": "a", "arguments": {"path": "src/a.rs"}},
            {"ordinal": 11, "kind": "tool_result", "tool_name": "exec_command", "call_id": "a", "exit_code": 1, "output": "failed"},
            {"ordinal": 12, "kind": "tool_result", "tool_name": "exec_command", "call_id": "b", "status": "success", "exit_code": 2, "output": "x" * 500},
            ["unsupported"],
        ]
        with path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record) + "\n")
            handle.write("{malformed\n")
        return path

    def run_query(self, path: Path, *arguments: str) -> tuple[int, str, dict[str, object]]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(path), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout, json.loads(result.stdout) if result.stdout else {}

    def test_filters_status_and_preserves_contradiction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_index(Path(directory))
            code, _, output = self.run_query(path, "--status", "ambiguous")
        self.assertEqual(code, 0)
        self.assertEqual(output["emitted_row_count"], 1)
        self.assertEqual(output["matched_rows"][0]["ordinal"], 12)
        self.assertEqual(output["matched_rows"][0]["status_evidence"], "explicit-status-conflicts-with-exit-code")

    def test_bounds_large_records_and_reports_malformed_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_index(Path(directory))
            code, first_text, output = self.run_query(path, "--record-bytes", "40", "--max-rows", "10")
            second_code, second_text, _ = self.run_query(path, "--record-bytes", "40", "--max-rows", "10")
        self.assertEqual(code, 0)
        self.assertEqual(second_code, 0)
        self.assertEqual(first_text, second_text)
        self.assertEqual(len(output["malformed"]), 1)
        self.assertEqual(len(output["unsupported"]), 1)
        self.assertTrue(any(row["record"].get("truncated") for row in output["matched_rows"]))

    def test_valid_zero_match_is_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_index(Path(directory))
            code, _, output = self.run_query(path, "--tool", "not-present")
        self.assertEqual(code, 0)
        self.assertEqual(output["emitted_row_count"], 0)

    def test_invalid_regex_is_typed_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_index(Path(directory))
            code, _, output = self.run_query(path, "--output-pattern", "[")
        self.assertEqual(code, 2)
        self.assertEqual(output["status"], "invalid-filter")


if __name__ == "__main__":
    unittest.main()
