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
                f"Read `{artifact}`.", environ={}, fallback_home=fallback_home
            )

            self.assertEqual(result.status, "success")
            self.assertEqual(result.artifact, goal_artifact_resolution.display_path(artifact))

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


class ExactPathTests(unittest.TestCase):
    """Protect path identity, explicit relative bases, and structured failures."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.runtime, self.attachments = goal_artifact_resolution.make_root(self.base)
        self.environment = {"CODEX_HOME": str(self.runtime)}

    def managed(self, objective: str) -> goal_artifact_resolution.GoalArtifactResolution:
        return goal_artifact_resolution.resolve_artifact(objective, environ=self.environment)

    def wrapper(self, artifact: Path | str) -> str:
        return f"pasted text file: {artifact}. Read this file before continuing."

    def test_complete_wrapper_and_quotes_preserve_names_including_prefix_decoys(self) -> None:
        for name in ("custom name.plan", "punctuated)", "trailing.", "trailing ", "apostrophe's goal", "no-extension"):
            with self.subTest(name=name):
                artifact = goal_artifact_resolution.make_artifact(self.attachments, name)
                prefix = name.split()[0].rstrip(".)")
                if prefix != name:
                    goal_artifact_resolution.make_artifact(self.attachments, prefix)
                for objective in (self.wrapper(artifact), f"Read `{artifact}`.", str(artifact)):
                    result = self.managed(objective)
                    self.assertEqual(result.status, "success")
                    self.assertEqual(result.artifact, goal_artifact_resolution.display_path(artifact))
                    self.assertEqual(artifact.read_text(encoding="utf-8"), "objective")

    def test_unbounded_prose_never_selects_a_shorter_existing_filename(self) -> None:
        artifact = goal_artifact_resolution.make_artifact(self.attachments, "long name)")
        goal_artifact_resolution.make_artifact(self.attachments, "long")
        result = self.managed(f"Read {artifact} before continuing.")
        self.assertEqual(result.code, "managed-path-shape")
        self.assertEqual(result.received, "unbounded-prose-reference")
        self.assertIsNone(result.artifact)

    def test_a_closing_phrase_inside_a_filename_cannot_select_a_wrapper_prefix(self) -> None:
        artifact = goal_artifact_resolution.make_artifact(
            self.attachments, "prefix. Read this file before continuing. suffix"
        )
        goal_artifact_resolution.make_artifact(self.attachments, "prefix")
        result = self.managed(self.wrapper(artifact))
        self.assertEqual(result.code, "managed-path-shape")
        self.assertIsNone(result.artifact)
        quoted = self.managed(f"Read `{artifact}`.")
        self.assertEqual(quoted.status, "success")
        self.assertEqual(Path(quoted.artifact).expanduser(), artifact)

    def test_wrappers_participate_in_unique_reference_selection(self) -> None:
        artifact = goal_artifact_resolution.make_artifact(self.attachments, "first goal")
        second = goal_artifact_resolution.make_artifact(self.attachments, "second")
        repeated = self.managed(f"{self.wrapper(artifact)} Again: `{artifact}`.")
        self.assertEqual(repeated.status, "success")
        self.assertEqual(repeated.candidate_count, 1)
        for extra in (f"`{second}`", self.wrapper(second), str(second)):
            result = self.managed(f"{self.wrapper(artifact)} Also {extra}")
            self.assertEqual(result.code, "ambiguous-managed-artifacts")
            self.assertEqual(result.candidate_count, 2)

    def test_wrapper_support_preserves_managed_shape_and_identity_guards(self) -> None:
        artifact = goal_artifact_resolution.make_artifact(self.attachments)
        internal = artifact.with_name("internal")
        internal.symlink_to(artifact)
        outside = self.base / "outside"
        outside.write_text("outside", encoding="utf-8")
        escape = artifact.with_name("escape")
        escape.symlink_to(outside)
        cases = (
            (internal, "artifact-not-file"),
            (escape, "attachments-root-mismatch"),
            (f"{artifact.parent}/nested/../goal", "managed-path-shape"),
            (artifact.with_name("missing"), "artifact-not-file"),
            (self.attachments / "not-a-uuid" / "goal", "managed-path-shape"),
        )
        for path, code in cases:
            with self.subTest(code=code):
                self.assertEqual(self.managed(self.wrapper(path)).code, code)
        other, _ = goal_artifact_resolution.make_root(self.base, "other")
        mismatch = goal_artifact_resolution.resolve_artifact(
            self.wrapper(artifact), environ={"CODEX_HOME": str(other)}
        )
        self.assertEqual(mismatch.code, "attachments-root-mismatch")
        linked = self.base / "linked-runtime"
        linked.mkdir()
        (linked / "attachments").symlink_to(self.attachments, target_is_directory=True)
        result = goal_artifact_resolution.resolve_artifact(
            self.wrapper(artifact), environ={"CODEX_HOME": str(linked)}
        )
        self.assertEqual(result.code, "invalid-runtime-root")

    def test_designated_files_accept_any_name_outside_managed_attachments(self) -> None:
        for name in ("custom plan.md", "cleanup", "review).", "pasted-text-42.other", " leading and trailing "):
            with self.subTest(name=name):
                artifact = self.base / name
                artifact.write_bytes(b"selected goal\n")
                for reference in (str(artifact), goal_artifact_resolution.display_path(artifact), name):
                    result = goal_artifact_resolution.resolve_designated_artifact(reference, base_dir=self.base)
                    self.assertEqual(result.status, "success")
                    self.assertEqual(Path(result.artifact).expanduser(), artifact)
                    self.assertEqual(result.approach, "designated-path")
                self.assertEqual(artifact.read_bytes(), b"selected goal\n")

    def test_whole_objective_paths_use_the_declared_base_independently_of_runtime(self) -> None:
        artifact = self.base / "plans" / "cleanup plan"
        artifact.parent.mkdir()
        artifact.write_text("goal", encoding="utf-8")
        for objective in (str(artifact), "./plans/cleanup plan", "`plans/cleanup plan`"):
            result = goal_artifact_resolution.resolve_artifact(
                objective, base_dir=self.base, environ={"CODEX_HOME": ""}
            )
            self.assertEqual(result.status, "success")
            self.assertEqual(Path(result.artifact).expanduser(), artifact)
        short = self.base / "plans" / "cleanup"
        short.write_text("decoy", encoding="utf-8")
        result = goal_artifact_resolution.resolve_artifact(
            "plans/cleanup", base_dir=self.base, environ={}
        )
        self.assertEqual(Path(result.artifact).expanduser(), short)

    def test_relative_paths_require_a_valid_explicit_base(self) -> None:
        for base in (None, "", "relative-base", self.base / "missing", [], "~nonexistent_goal_user_7d1ca951"):
            with self.subTest(base_type=type(base).__name__):
                result = goal_artifact_resolution.resolve_designated_artifact("goal", base_dir=base)
                self.assertEqual(result.code, "invalid-goal-base")
                self.assertIsNone(result.artifact)

    def test_arbitrary_prose_mentions_are_not_goal_path_designations(self) -> None:
        artifact = self.base / "historical-goal.md"
        artifact.write_text("history", encoding="utf-8")
        result = self.managed(f"Compare history at `{artifact}` while doing the current work.")
        self.assertEqual(result.code, "no-managed-artifact-reference")

    def test_invalid_designated_paths_remain_typed(self) -> None:
        for reference in (None, 5, "", "   "):
            self.assertEqual(goal_artifact_resolution.resolve_designated_artifact(reference).code, "invalid-goal-path")
        for path in (self.base / "missing", self.base):
            self.assertEqual(goal_artifact_resolution.resolve_designated_artifact(str(path)).code, "artifact-not-file")
        target = self.base / "actual"
        target.write_text("goal", encoding="utf-8")
        alias = self.base / "alias"
        alias.symlink_to(target)
        result = goal_artifact_resolution.resolve_designated_artifact(str(alias))
        self.assertEqual(result.received, "symlink")

    def test_cli_keeps_expansion_errors_structured_and_paths_normalized(self) -> None:
        missing_home = "~nonexistent_goal_user_7d1ca951"
        artifact = goal_artifact_resolution.make_artifact(self.attachments)
        cases = (
            (["--objective", self.wrapper(artifact)], {"CODEX_HOME": missing_home}, "invalid-runtime-root"),
            (["--objective", self.wrapper(f"{missing_home}/attachments/{UUID}/goal")], self.environment, "artifact-path-unresolvable"),
            (["--goal-path", f"{missing_home}/goal"], self.environment, "artifact-path-unresolvable"),
            (["--goal-path", "relative-goal"], self.environment, "invalid-goal-base"),
            (["--goal-path", str(artifact)], self.environment, "resolved-exact-artifact"),
            (["--goal-path", artifact.name, "--base-dir", str(artifact.parent)], self.environment, "resolved-exact-artifact"),
            (["--objective", str(artifact)], self.environment, "resolved-exact-artifact"),
        )
        for arguments, environment, code in cases:
            with self.subTest(code=code, mode=arguments[0]):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT_DIRECTORY / "goal_artifact_resolution.py"), *arguments],
                    env={**os.environ, **environment}, capture_output=True, text=True, check=False,
                )
                output = json.loads(result.stdout)
                self.assertEqual(output["code"], code)
                self.assertEqual(result.returncode, 0 if output["status"] == "success" else 1)
                self.assertEqual(result.stderr, "")
                self.assertNotIn(str(Path.home()) + "/", result.stdout)

    def test_cli_rejects_conflicting_selection_modes_before_resolution(self) -> None:
        for arguments in (
            [],
            ["--objective", "./first", "--goal-path", "./second"],
            ["--self-test", "--base-dir", str(self.base)],
        ):
            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIRECTORY / "goal_artifact_resolution.py"), *arguments],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
            self.assertIn("error:", result.stderr)


class DiagnosticPresentationTests(unittest.TestCase):
    """Keep home-path presentation separate from the identity of other text."""

    def test_diagnostic_values_preserve_sibling_paths_and_nested_values(self) -> None:
        home = str(Path.home().resolve(strict=False))
        siblings = [home + suffix for suffix in ("-neighbor/goal", ".backup", " archive/goal", "'archive/goal")]
        unrelated = [f"/mirror{home}/goal", f"label{home}/goal", "~/already-normalized"]
        value = {home: [home, f"{home}/goal", siblings, unrelated, None, False, 0, ""]}

        rendered = json.loads(goal_completion_handoff_hook.render_value(value))

        self.assertEqual(rendered, {"~": ["~", "~/goal", siblings, unrelated, None, False, 0, ""]})

    def test_accounting_normalizes_delimited_paths_without_rewriting_other_text(self) -> None:
        home = str(Path.home().resolve(strict=False))
        report = f'Retain `{home}/goal`, root "{home}", sibling `{home}-neighbor/goal`, and label{home}/goal.'
        expected = f'Retain `~/goal`, root "~", sibling `{home}-neighbor/goal`, and label{home}/goal.'

        context = goal_completion_handoff_hook.accounting_context(
            {"tokensUsed": 41, "timeUsedSeconds": 9},
            {"completionBudgetReport": report},
        )

        self.assertIn(f"completion requirement: {expected}", context)
        self.assertIn("`goal.tokensUsed=41`", context)
        self.assertIn("`goal.timeUsedSeconds=9`", context)


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

    def test_path_expansion_failure_still_emits_the_typed_handoff_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "attachments").mkdir()
            payload = self.completion_payload(
                f"~nonexistent_goal_user_7d1ca951/attachments/{UUID}/goal"
            )
            result = self.run_hook(payload, codex_home=root)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Code: artifact-path-unresolvable", context)
            self.assertIn("Candidate count: 1", context)

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
