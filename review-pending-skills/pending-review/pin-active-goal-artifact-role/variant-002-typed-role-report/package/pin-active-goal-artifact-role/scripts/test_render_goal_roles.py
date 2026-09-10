#!/usr/bin/env python3
"""Behavioral tests for literal reference identity and declared role attribution."""

import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import render_goal_roles as report


class GoalRoleTests(unittest.TestCase):
    def test_complete_path_spellings_and_relative_goal_base(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            goal = root / "plans" / "active.md"
            goal.parent.mkdir()
            artifact = root / "evidence" / "run.json"
            for mention in (f"`{artifact}`", "[report](../evidence/run.json)", "`./../evidence/run.json`"):
                with self.subTest(mention=mention):
                    source = ("intro\rstill line one\n" + mention).encode()
                    goal.write_bytes(source)
                    result = report.build_report(str(goal), [f"historical={artifact}"])
                    entry = result["references"][0]
                    self.assertEqual(entry["reference_lines"], [2])
                    self.assertEqual(entry["role_source"], "caller-declared")
                    self.assertTrue(entry["text_reference_verified"])
                    self.assertFalse(entry["artifact_contents_verified"])
                    self.assertFalse(artifact.exists())
                    self.assertEqual(result["active"]["sha256"], hashlib.sha256(source).hexdigest())

    def test_prefix_and_wrong_directory_mentions_do_not_verify(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            goal = root / "active.md"
            artifact = root / "other" / "goal.md"
            for mention in (f"`{artifact}.backup`", f"`/mirror{artifact}`", "`goal.md`", f"[link]({artifact}#heading)"):
                with self.subTest(mention=mention):
                    goal.write_text(mention)
                    with self.assertRaises(report.RoleError):
                        report.build_report(str(goal), [f"evidence={artifact}"])

    def test_home_spelling_verifies_without_reading_secondary_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            goal = Path(temporary) / "active.md"
            goal.write_text('Historical reference: `~/unread-role-test/input.md`')
            result = report.build_report(str(goal), ['evidence=~/unread-role-test/input.md'])
            self.assertEqual(result["references"][0]["role"], "evidence")
            self.assertEqual(result["references"][0]["role_source"], "caller-declared")

    def test_duplicate_roles_and_active_alias_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            goal = root / "active.md"
            reference = root / "previous.md"
            goal.write_text(f"`{reference}`")
            for references in ([f"evidence={goal}"], [f"evidence={reference}", f"historical={reference}"]):
                with self.subTest(references=references), self.assertRaises(report.RoleError):
                    report.build_report(str(goal), references)

    def test_cli_failure_preserves_error_channel_and_normalizes_home(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path.home() / Path(temporary).name / "missing.md"
            result = subprocess.run([sys.executable, report.__file__, '--active', str(missing)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            self.assertIn('~/', result.stderr)
            self.assertNotIn(str(Path.home()) + '/', result.stderr)


if __name__ == '__main__':
    unittest.main()
