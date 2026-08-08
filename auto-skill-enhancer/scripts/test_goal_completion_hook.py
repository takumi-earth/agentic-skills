#!/usr/bin/env python3
"""Focused tests for the post-goal completion hook."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

import goal_completion_hook


HOOK = Path(goal_completion_hook.__file__).resolve()


class GoalFileResolutionTests(unittest.TestCase):
    def test_uses_the_single_file_exposed_by_the_goal_object(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary)
            attachment_dir = codex_home / "attachments" / str(uuid4())
            attachment_dir.mkdir(parents=True)
            exposed_file = attachment_dir / "arbitrary-durable-ledger.data"
            exposed_file.write_text("goal", encoding="utf-8")

            resolved = goal_completion_hook.referenced_goal_file(
                {"objective": f"The goal object exposes {exposed_file}."},
                codex_home,
            )

            self.assertEqual(resolved, exposed_file.resolve())

    def test_rejects_an_ambiguous_goal_object(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary)
            attachment_dir = codex_home / "attachments" / str(uuid4())
            attachment_dir.mkdir(parents=True)
            first = attachment_dir / "first"
            second = attachment_dir / "second"
            first.write_text("first", encoding="utf-8")
            second.write_text("second", encoding="utf-8")

            resolved = goal_completion_hook.referenced_goal_file(
                {"objective": f"Use {first} and {second}."},
                codex_home,
            )

            self.assertIsNone(resolved)

    def test_rejects_a_managed_symlink_that_escapes_attachments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary)
            attachment_dir = codex_home / "attachments" / str(uuid4())
            attachment_dir.mkdir(parents=True)
            outside = codex_home / "outside"
            outside.write_text("outside", encoding="utf-8")
            exposed_file = attachment_dir / "ledger"
            exposed_file.symlink_to(outside)

            resolved = goal_completion_hook.referenced_goal_file(
                {"objective": f"Use {exposed_file}."},
                codex_home,
            )

            self.assertIsNone(resolved)


class HookOutputTests(unittest.TestCase):
    def run_hook(self, payload: object) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )

    def test_noncomplete_goal_emits_no_context(self) -> None:
        result = self.run_hook(
            {
                "tool_input": {"status": "blocked"},
                "tool_response": {"goal": {"status": "blocked"}},
            }
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_goal_without_exposed_file_skips_review(self) -> None:
        result = self.run_hook(
            {
                "session_id": "session",
                "transcript_path": "/tmp/session.jsonl",
                "tool_input": {"status": "complete"},
                "tool_response": {
                    "goal": {
                        "status": "complete",
                        "objective": "A short inline goal",
                        "tokensUsed": 12,
                        "timeUsedSeconds": 3,
                    }
                },
            }
        )

        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertIn("did not expose an exact managed harness goal file", context)
        self.assertIn("Do not run the automatic post-goal skill review", context)
        self.assertIn("`goal.tokensUsed=12`", context)
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
