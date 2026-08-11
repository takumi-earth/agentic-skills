#!/usr/bin/env python3
"""Behavior and topology tests for the automatic post-goal review hook."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIRECTORY.parent
REPOSITORY_ROOT = PACKAGE_ROOT.parent
sys.path.insert(0, str(SCRIPT_DIRECTORY))

import post_goal_review_hook  # noqa: E402


HOOK = SCRIPT_DIRECTORY / "post_goal_review_hook.py"
HANDOFF_HOOK = (
    REPOSITORY_ROOT
    / "maintain-living-goal"
    / "scripts"
    / "goal_completion_handoff_hook.py"
)
UUID = "12345678-1234-1234-1234-123456789abc"


class PostGoalReviewHookTests(unittest.TestCase):
    """Exercise automatic-review gating and separation from the handoff owner."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.codex_home = self.root / "codex"
        self.artifact = self.codex_home / "attachments" / UUID / "living-goal.txt"
        self.artifact.parent.mkdir(parents=True)
        self.artifact.write_text("goal\n", encoding="utf-8")
        self.transcript = self.root / "session.jsonl"
        self.transcript.write_text("{}\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def payload(self) -> dict[str, object]:
        return {
            "session_id": "session-123",
            "transcript_path": str(self.transcript),
            "tool_input": {"status": "complete"},
            "tool_response": {
                "goal": {
                    "status": "complete",
                    "goalId": "goal-123",
                    "objective": f"Continue from `{self.artifact}`.",
                    "tokensUsed": 41,
                    "timeUsedSeconds": 9,
                }
            },
        }

    def run_hook(
        self,
        script: Path,
        payload: object,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["CODEX_HOME"] = str(self.codex_home)
        return subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=environment,
        )

    def test_success_emits_only_review_context_and_requires_the_handoff_marker(self) -> None:
        before = self.artifact.read_bytes()

        result = self.run_hook(HOOK, self.payload())

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        output = json.loads(result.stdout)
        self.assertEqual(set(output), {"hookSpecificOutput"})
        hook_output = output["hookSpecificOutput"]
        self.assertEqual(set(hook_output), {"hookEventName", "additionalContext"})
        self.assertEqual(hook_output["hookEventName"], "PostToolUse")
        context = hook_output["additionalContext"]
        self.assertIn("automatic post-completion skill review", context)
        self.assertIn("codex-goal-completion-handoff:goal-123:begin", context)
        self.assertIn("codex-goal-completion-handoff:goal-123:end", context)
        self.assertIn("written to and re-read", context)
        self.assertIn("skip the automatic review", context)
        self.assertIn("--exclude-skill auto-skill-enhancer", context)
        self.assertIn("session-123", context)
        self.assertIn(str(self.transcript), context)
        self.assertNotIn("Checked condition:", context)
        self.assertNotIn("Expected:", context)
        self.assertNotIn("Structured completion accounting", context)
        self.assertNotIn("Append that text exactly once", context)
        self.assertEqual(self.artifact.read_bytes(), before)

    def test_noncompletion_missing_inputs_and_resolution_failure_are_silent(self) -> None:
        cases = []
        noncompletion = self.payload()
        noncompletion["tool_input"] = {"status": "blocked"}
        cases.append(noncompletion)
        no_session = self.payload()
        no_session.pop("session_id")
        cases.append(no_session)
        no_transcript = self.payload()
        no_transcript.pop("transcript_path")
        cases.append(no_transcript)
        no_artifact = self.payload()
        no_artifact["tool_response"]["goal"]["objective"] = "Inline objective only"
        cases.append(no_artifact)

        for payload in cases:
            with self.subTest(payload=payload):
                result = self.run_hook(HOOK, payload)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "")

    def test_both_handlers_resolve_identical_immutable_inputs_independently(self) -> None:
        scripts = REPOSITORY_ROOT / "maintain-living-goal" / "scripts"
        sys.path.insert(0, str(scripts))
        try:
            import goal_artifact_resolution

            with patch.dict(
                os.environ, {"CODEX_HOME": str(self.codex_home)}, clear=False
            ):
                owner_result = goal_artifact_resolution.resolve_artifact(
                    self.payload()["tool_response"]["goal"]["objective"]
                )
                review_result = post_goal_review_hook.resolve_goal(
                    self.payload()["tool_response"]["goal"]
                )
        finally:
            sys.path.remove(str(scripts))

        self.assertIsNotNone(review_result)
        self.assertEqual(review_result.status, owner_result.status)
        self.assertEqual(review_result.code, owner_result.code)
        self.assertEqual(review_result.artifact, owner_result.artifact)

    def test_handlers_emit_separate_contexts_with_distinct_purposes(self) -> None:
        handoff = self.run_hook(HANDOFF_HOOK, self.payload())
        review = self.run_hook(HOOK, self.payload())

        self.assertEqual(handoff.returncode, 0)
        self.assertEqual(review.returncode, 0)
        handoff_context = json.loads(handoff.stdout)["hookSpecificOutput"][
            "additionalContext"
        ]
        review_context = json.loads(review.stdout)["hookSpecificOutput"][
            "additionalContext"
        ]
        self.assertIn("Append that text exactly once", handoff_context)
        self.assertNotIn("automatic post-completion skill review", handoff_context)
        self.assertIn("automatic post-completion skill review", review_context)
        self.assertNotIn("Append that text exactly once", review_context)


class SiblingTopologyTests(unittest.TestCase):
    """Exercise the declared sibling resource under copied and linked packages."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.codex_home = self.root / "codex"
        self.artifact = self.codex_home / "attachments" / UUID / "goal"
        self.artifact.parent.mkdir(parents=True)
        self.artifact.write_text("goal\n", encoding="utf-8")
        self.transcript = self.root / "session.jsonl"
        self.transcript.write_text("{}\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def payload(self) -> dict[str, object]:
        return {
            "session_id": "topology-session",
            "transcript_path": str(self.transcript),
            "tool_input": {"status": "complete"},
            "tool_response": {
                "goal": {
                    "status": "complete",
                    "goalId": "topology-goal",
                    "objective": f"Use `{self.artifact}`.",
                }
            },
        }

    def run_fixture(self, script: Path) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["CODEX_HOME"] = str(self.codex_home)
        return subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps(self.payload()),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=environment,
        )

    def create_topology(self, name: str) -> Path:
        fixture = self.root / name
        fixture.mkdir()
        if name == "copied":
            shutil.copytree(PACKAGE_ROOT, fixture / "auto-skill-enhancer")
            shutil.copytree(
                REPOSITORY_ROOT / "maintain-living-goal",
                fixture / "maintain-living-goal",
            )
        else:
            auto_target = PACKAGE_ROOT
            owner_target = REPOSITORY_ROOT / "maintain-living-goal"
            if name == "relative-symlink":
                auto_target = Path(os.path.relpath(auto_target, fixture))
                owner_target = Path(os.path.relpath(owner_target, fixture))
            os.symlink(auto_target, fixture / "auto-skill-enhancer")
            os.symlink(owner_target, fixture / "maintain-living-goal")
        return fixture / "auto-skill-enhancer" / "scripts" / "post_goal_review_hook.py"

    def test_canonical_copy_relative_and_absolute_topologies_match_behavior(self) -> None:
        scripts = {
            "canonical-direct": HOOK,
            "copied": self.create_topology("copied"),
            "relative-symlink": self.create_topology("relative-symlink"),
            "absolute-symlink": self.create_topology("absolute-symlink"),
        }

        for name, script in scripts.items():
            with self.subTest(topology=name):
                result = self.run_fixture(script)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stderr, "")
                context = json.loads(result.stdout)["hookSpecificOutput"][
                    "additionalContext"
                ]
                self.assertIn("automatic post-completion skill review", context)
                self.assertIn("topology-goal", context)

    def test_missing_sibling_is_a_silent_noop(self) -> None:
        fixture = self.root / "missing-sibling"
        shutil.copytree(PACKAGE_ROOT, fixture / "auto-skill-enhancer")
        script = fixture / "auto-skill-enhancer" / "scripts" / "post_goal_review_hook.py"

        result = self.run_fixture(script)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
