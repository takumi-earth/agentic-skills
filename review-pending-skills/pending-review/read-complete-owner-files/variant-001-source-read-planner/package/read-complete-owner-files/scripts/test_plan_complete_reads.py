#!/usr/bin/env python3
"""Focused tests for deterministic complete-source read planning."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIRECTORY))

import plan_complete_reads


PLANNER = SCRIPT_DIRECTORY / "plan_complete_reads.py"


class CompleteReadPlanTests(unittest.TestCase):
    def test_unterminated_final_line_is_counted_and_ranges_cover_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "owner.txt"
            path.write_bytes(b"alpha\nbeta\ngamma")

            plan = plan_complete_reads.plan_file(path, max_chunk_bytes=7)

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

    def test_batched_preflight_never_emits_source_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first.txt"
            second = root / "second.toml"
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
            self.assertNotIn("private-first-body", result.stdout)
            self.assertNotIn("private-second-body", result.stdout)

    def test_empty_file_has_no_ranges(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "empty.txt"
            path.write_bytes(b"")

            plan = plan_complete_reads.plan_file(path, max_chunk_bytes=8)

            self.assertEqual(plan["logical_line_count"], 0)
            self.assertEqual(plan["chunks"], [])
            self.assertEqual(plan["byte_count"], 0)

    def test_oversized_single_line_is_flagged_without_splitting(self) -> None:
        chunks = plan_complete_reads.chunk_lines(
            [b"short\n", b"0123456789abcdef\n", b"tail\n"],
            max_chunk_bytes=8,
        )

        self.assertEqual(
            [(chunk["start_line"], chunk["end_line"]) for chunk in chunks],
            [(1, 1), (2, 2), (3, 3)],
        )
        self.assertEqual(
            [chunk["oversized_line"] for chunk in chunks],
            [False, True, False],
        )

    def test_duplicate_resolved_files_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "owner.txt"
            alias = root / "alias.txt"
            path.write_text("body\n", encoding="utf-8")
            alias.symlink_to(path)

            with self.assertRaisesRegex(ValueError, "resolve to unique"):
                plan_complete_reads.build_plan([path, alias], 100)

    def test_home_paths_are_normalized(self) -> None:
        path = Path.home() / "work" / "owner.txt"

        self.assertEqual(plan_complete_reads.display_path(path), "~/work/owner.txt")


if __name__ == "__main__":
    unittest.main()
