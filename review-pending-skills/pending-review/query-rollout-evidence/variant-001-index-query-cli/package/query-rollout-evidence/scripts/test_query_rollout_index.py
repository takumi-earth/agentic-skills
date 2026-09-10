#!/usr/bin/env python3
"""Direct tests for query_rollout_index.py."""

from __future__ import annotations

import json
import hashlib
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

    def test_supported_envelopes_keep_payload_data_out_of_selectors(self) -> None:
        records = [
            {"type": "message", "role": "user", "content": {"status": "failed", "tool_name": "forged", "call_id": "fake", "ordinal": 99, "note": "unselected-path"}},
            {"kind": "tool_call", "id": "fallback", "tool_name": "exec", "status": "ambiguous", "arguments": {"command": "argument-only", "path": "src/owned.rs"}},
            {"type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec", "call_id": "nested", "input": "command"}},
            {"kind": "tool_result", "status": "completed", "exit_code": 9, "output": "actual-output"},
            {"kind": "tool_result", "status": "completed", "output": "Done!"},
        ]
        cases = (
            (("--tool", "forged"), []),
            (("--call-id", "fallback"), ["ambiguous"]),
            (("--call-id", "nested"), ["attempted"]),
            (("--output-pattern", "argument-only"), []),
            (("--output-pattern", "^actual-output$"), ["failed"]),
            (("--path-contains", "unselected-path"), []),
            (("--path-contains", "src/owned"), ["ambiguous"]),
            (("--status", "failed"), ["failed"]),
            (("--status", "unknown"), ["unknown"]),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.jsonl"
            path.write_text("".join(json.dumps(record) + "\n" for record in records))
            for arguments, statuses in cases:
                with self.subTest(arguments=arguments):
                    code, _, output = self.run_query(path, *arguments)
                    self.assertEqual(code, 0)
                    self.assertEqual([row["status"] for row in output["matched_rows"]], statuses)

    def test_lf_anchors_total_budget_and_deep_input_are_explicit(self) -> None:
        source = b'{}\r{}\n{"ordinal":3,"kind":"message"}\n' + b'{malformed\n' * 100
        source += b'[' * 1200 + b'0' + b']' * 1200 + b'\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.jsonl"
            path.write_bytes(source)
            code, _, output = self.run_query(path, "--ordinal-min", "3", "--ordinal-max", "3")
            self.assertEqual(code, 0)
            self.assertEqual(output["matched_rows"][0]["source_line"], 2)
            self.assertEqual(output["source_sha256"], hashlib.sha256(source).hexdigest())
            code, text, output = self.run_query(path, "--max-rows", "0", "--max-bytes", "128")
            self.assertEqual(code, 0)
            self.assertLessEqual(len(text.encode("utf-8")), 128)
            self.assertGreater(output["omitted"][1], 0)
            self.assertEqual(output["omitted"][0], 1)
            code, _, output = self.run_query(path, "--ordinal-min", "5", "--ordinal-max", "2")
            self.assertEqual(code, 2)
            self.assertEqual(output["status"], "invalid-filter")

    def test_presentation_keeps_original_evidence_hashes(self) -> None:
        home = str(Path.home().resolve(strict=False))
        record = {"kind": "message", "content": f"Read `{home}/evidence`."}
        source = (json.dumps(record) + "\n").encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.jsonl"
            path.write_bytes(source)
            code, text, output = self.run_query(path)
        self.assertEqual(code, 0)
        self.assertNotIn(home + "/", text)
        self.assertEqual(output["source_sha256"], hashlib.sha256(source).hexdigest())
        canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.assertEqual(output["matched_rows"][0]["record_hash"], hashlib.sha256(canonical).hexdigest())
        code, text, output = self.run_query(Path.home() / "missing-rollout-fixture-657b2eb0")
        self.assertEqual(code, 2)
        self.assertNotIn(home + "/", text)
        self.assertEqual(output["status"], "error")


if __name__ == "__main__":
    unittest.main()
