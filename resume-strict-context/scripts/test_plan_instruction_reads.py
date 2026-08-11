#!/usr/bin/env python3
"""Focused tests for deterministic instruction-read planning."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIRECTORY))

import plan_instruction_reads  # noqa: E402


PLANNER = SCRIPT_DIRECTORY / "plan_instruction_reads.py"


class InstructionReadPlanTests(unittest.TestCase):
    def test_unterminated_final_line_is_counted_and_ranges_cover_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "SKILL.md"
            path.write_bytes(b"alpha\nbeta\ngamma")

            plan = plan_instruction_reads.plan_file(path, max_chunk_bytes=7)

            self.assertEqual(plan["logical_line_count"], 3)
            self.assertFalse(plan["ends_with_newline"])
            self.assertEqual(
                [(chunk["start_line"], chunk["end_line"]) for chunk in plan["chunks"]],
                [(1, 1), (2, 2), (3, 3)],
            )
            self.assertEqual(
                sum(chunk["byte_count"] for chunk in plan["chunks"]),
                plan["byte_count"],
            )

    def test_batched_preflight_emits_metadata_without_instruction_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first.md"
            second = root / "second.md"
            first.write_text("private-first-body\n", encoding="utf-8")
            second.write_text("private-second-body\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(PLANNER), str(first), str(second)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            output = json.loads(result.stdout)
            self.assertEqual(output["file_count"], 2)
            self.assertFalse(output["content_emitted"])
            self.assertEqual(
                [file_plan["path"] for file_plan in output["files"]],
                [str(first), str(second)],
            )
            self.assertNotIn("private-first-body", result.stdout)
            self.assertNotIn("private-second-body", result.stdout)

    def test_oversized_single_line_is_flagged_without_splitting_it(self) -> None:
        lines = [b"short\n", b"0123456789abcdef\n", b"tail\n"]

        chunks = plan_instruction_reads.chunk_lines(lines, max_chunk_bytes=8)

        self.assertEqual(
            [(chunk["start_line"], chunk["end_line"]) for chunk in chunks],
            [(1, 1), (2, 2), (3, 3)],
        )
        self.assertEqual(
            [chunk["oversized_line"] for chunk in chunks],
            [False, True, False],
        )

    def test_duplicate_lexical_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "skill.md"
            path.write_text("body\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "must be unique"):
                plan_instruction_reads.build_plan([path, path], 100)

    def test_home_paths_are_normalized(self) -> None:
        path = Path.home() / ".codex" / "skills" / "example" / "SKILL.md"

        self.assertEqual(
            plan_instruction_reads.display_path(path),
            "~/.codex/skills/example/SKILL.md",
        )


if __name__ == "__main__":
    unittest.main()
