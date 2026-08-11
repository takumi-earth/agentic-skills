#!/usr/bin/env python3
"""Behavior tests for goal-artifact resolution and completion handoff."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIRECTORY))

import goal_artifact_resolution  # noqa: E402
import goal_completion_handoff_hook  # noqa: E402


HOOK = SCRIPT_DIRECTORY / "goal_completion_handoff_hook.py"
UUID = "12345678-1234-1234-1234-123456789abc"


class ResolverTests(unittest.TestCase):
    """Exercise the pure runtime-root and artifact-resolution contract."""

    def test_packaged_self_test_covers_every_stable_code(self) -> None:
        result = goal_artifact_resolution.self_test()

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["assertions"], 25)

    def test_custom_runtime_result_is_repeatable_and_side_effect_free(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "codex"
            artifact = root / "attachments" / UUID / "goal.plan"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("goal\n", encoding="utf-8")
            before = artifact.read_bytes()
            objective = f"Read `{artifact}` through EOF."

            first = goal_artifact_resolution.resolve_artifact(
                objective, environ={"CODEX_HOME": str(root)}
            )
            second = goal_artifact_resolution.resolve_artifact(
                objective, environ={"CODEX_HOME": str(root)}
            )

            self.assertEqual(first, second)
            self.assertEqual(first.status, "success")
            self.assertEqual(first.code, "resolved-exact-artifact")
            self.assertEqual(artifact.read_bytes(), before)

    def test_unset_runtime_uses_only_the_home_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fallback_home = Path(temporary)
            artifact = fallback_home / ".codex" / "attachments" / UUID / "goal"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("goal\n", encoding="utf-8")

            result = goal_artifact_resolution.resolve_artifact(
                f"Read {artifact}.", environ={}, fallback_home=fallback_home
            )

            self.assertEqual(result.status, "success")
            self.assertEqual(result.artifact, str(artifact))

    def test_empty_configured_runtime_does_not_fall_back(self) -> None:
        result = goal_artifact_resolution.resolve_artifact(
            "No authority may be inferred.",
            environ={"CODEX_HOME": ""},
            fallback_home=Path.home(),
        )

        self.assertEqual(result.status, "failure")
        self.assertEqual(result.code, "invalid-runtime-root")
        self.assertEqual(result.received["state"], "empty")

    def test_home_paths_are_normalized_for_serialization(self) -> None:
        rendered = goal_artifact_resolution.display_path(
            Path.home() / ".codex" / "attachments" / UUID / "goal"
        )

        self.assertEqual(rendered, f"~/.codex/attachments/{UUID}/goal")


class HandoffHookTests(unittest.TestCase):
    """Exercise trigger gating, output shape, diagnostics, and non-mutation."""

    def run_hook(
        self,
        payload: object,
        *,
        codex_home: Path | None = None,
        raw_input: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        if codex_home is not None:
            environment["CODEX_HOME"] = str(codex_home)
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload) if raw_input is None else raw_input,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=environment,
        )

    def completion_payload(self, artifact: Path | str) -> dict[str, object]:
        return {
            "session_id": "session-123",
            "tool_input": {"status": "complete"},
            "tool_response": {
                "goal": {
                    "status": "complete",
                    "goalId": "goal-123",
                    "objective": f"Continue from `{artifact}` after reading it fully.",
                    "tokensUsed": 41,
                    "tokenBudget": 100,
                    "timeUsedSeconds": 9,
                },
                "completionBudgetReport": "Final token usage: 41 of 100.",
            },
        }

    def test_success_needs_no_transcript_and_does_not_write_the_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "codex"
            artifact = root / "attachments" / UUID / "living-goal.txt"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("original goal\n", encoding="utf-8")
            before = artifact.read_bytes()

            result = self.run_hook(self.completion_payload(artifact), codex_home=root)

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            output = json.loads(result.stdout)
            self.assertEqual(set(output), {"hookSpecificOutput"})
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(
                set(hook_output), {"hookEventName", "additionalContext"}
            )
            self.assertEqual(hook_output["hookEventName"], "PostToolUse")
            context = hook_output["additionalContext"]
            self.assertIn("codex-goal-completion-handoff:goal-123:begin", context)
            self.assertIn("codex-goal-completion-handoff:goal-123:end", context)
            self.assertIn("`goal.tokensUsed=41`", context)
            self.assertIn("`goal.tokenBudget=100`", context)
            self.assertIn("`goal.timeUsedSeconds=9`", context)
            self.assertIn("Append that text exactly once", context)
            self.assertIn("Re-read the saved block", context)
            self.assertNotIn("auto-skill-enhancer", context)
            self.assertEqual(artifact.read_bytes(), before)

    def test_resolution_failure_renders_every_typed_field_and_fails_open(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "codex"
            (root / "attachments").mkdir(parents=True)
            payload = self.completion_payload("No managed artifact")
            payload["tool_response"]["goal"]["objective"] = "Inline objective only"

            result = self.run_hook(payload, codex_home=root)

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            context = json.loads(result.stdout)["hookSpecificOutput"][
                "additionalContext"
            ]
            self.assertIn("Checked condition:", context)
            self.assertIn("Expected:", context)
            self.assertIn("Received:", context)
            self.assertIn("Stage: parse-goal-objective", context)
            self.assertIn("Code: no-managed-artifact-reference", context)
            self.assertIn("Candidate count: 0", context)
            self.assertIn("ordinary goal-completion response", context)
            self.assertIn("downstream post-completion work", context)
            self.assertIn("`goal.tokensUsed=41`", context)
            self.assertIn("`goal.tokenBudget=100`", context)
            self.assertIn("`goal.timeUsedSeconds=9`", context)
            self.assertIn(
                "completion requirement: Final token usage: 41 of 100.",
                context,
            )
            self.assertNotIn("auto-skill-enhancer", context)

    def test_noncompletion_and_malformed_input_are_silent_noops(self) -> None:
        noncompletion = self.run_hook(
            {
                "tool_input": {"status": "blocked"},
                "tool_response": {"goal": {"status": "blocked"}},
            }
        )
        malformed = self.run_hook({}, raw_input="not-json")

        for result in (noncompletion, malformed):
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")

    def test_json_encoded_tool_objects_preserve_the_completion_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "codex"
            artifact = root / "attachments" / UUID / "goal"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("goal\n", encoding="utf-8")
            payload = self.completion_payload(artifact)
            payload["tool_input"] = json.dumps(payload["tool_input"])
            payload["tool_response"] = json.dumps(payload["tool_response"])

            result = self.run_hook(payload, codex_home=root)

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            self.assertEqual(
                json.loads(result.stdout)["hookSpecificOutput"]["hookEventName"],
                "PostToolUse",
            )


if __name__ == "__main__":
    unittest.main()
