#!/usr/bin/env python3
"""Direct tests for audit_review_effects.py."""

from __future__ import annotations

import json
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("audit_review_effects.py")


class ReviewSurfaceAuditorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        result = subprocess.run(
            ["git", "-C", str(SCRIPT.resolve().parent), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        cls.scratchpad = Path(result.stdout.strip()) / ".scratchpad"

    def temporary_directory(self) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory(prefix="review-effects-", dir=self.scratchpad)

    def invoke(self, package: Path) -> tuple[int, dict[str, object]]:
        before = {
            p.relative_to(package): p.read_bytes()
            for p in package.rglob("*")
            if p.is_file() and not p.is_symlink()
        }
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(package), "--json"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stderr, "", result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["schema_version"], 1)
        self.assertFalse(output["mutated_package"])
        self.assertEqual(
            before,
            {
                p.relative_to(package): p.read_bytes()
                for p in package.rglob("*")
                if p.is_file() and not p.is_symlink()
            },
        )
        return result.returncode, output

    def run_audit(self, skill_body: str, reference: str | None = None) -> tuple[int, dict[str, object]]:
        with self.temporary_directory() as directory:
            package = Path(directory) / "skill"
            package.mkdir()
            (package / "SKILL.md").write_text(skill_body, encoding="utf-8")
            if reference is not None:
                refs = package / "references"
                refs.mkdir()
                (refs / "policy.md").write_text(reference, encoding="utf-8")
            return self.invoke(package)

    def test_allows_inline_only_review(self) -> None:
        code, output = self.run_audit("# Skill\n\nReview the named source and return findings inline.\n")
        self.assertEqual(code, 0, output)
        self.assertEqual(output["findings"], [])

    def test_flags_persistence_and_probe_coupling(self) -> None:
        code, output = self.run_audit(
            "# Skill\n\nWhen you review a package, always write a report to `.scratchpad/`.\n"
            "Run tests and validation as part of the review.\n"
        )
        self.assertEqual(code, 1)
        rules = {finding["rule"] for finding in output["findings"]}
        self.assertIn("implicit-persistence", rules)
        self.assertIn("implicit-execution", rules)
        self.assertFalse(output["mutated_package"])

    def test_allows_explicit_persisted_deliverable_and_helper(self) -> None:
        code, output = self.run_audit(
            "# Skill\n\nWhen the user explicitly requests a persisted review report, write that report.\n"
            "Only when the user explicitly asks for collector output, run the collector helper.\n"
        )
        self.assertEqual(code, 0, output)
        self.assertEqual(output["findings"], [])

    def test_flags_unauthorized_remediation_and_git(self) -> None:
        code, output = self.run_audit(
            "# Skill\n\nAudit the package and apply fixes.\nStage and commit the remediation.\n"
        )
        self.assertEqual(code, 1)
        rules = {finding["rule"] for finding in output["findings"]}
        self.assertIn("implicit-mutation", rules)
        self.assertIn("implicit-git", rules)

    def test_scans_direct_markdown_reference(self) -> None:
        code, output = self.run_audit(
            "# Skill\n\nReview according to [the policy](references/policy.md).\n",
            "During every audit, automatically install and enable the helper.\n",
        )
        self.assertEqual(code, 1)
        self.assertEqual(output["findings"][0]["path"], "references/policy.md")
        self.assertEqual(output["findings"][0]["rule"], "implicit-activation")

    def test_review_authority_does_not_suppress_other_effects(self) -> None:
        cases = (
            "When the user explicitly requests a review, write a report.\n",
            "If the user asks for a review of a report, write a ledger.\n",
            "Review the package and write a report.\nDo not commit.\n",
            "Do not commit.\nReview the package and write a report.\n",
            "Review the package; do not commit, but write a report.\n",
            "Review the package.\n\nAlways write a report.\n",
        )
        for body in cases:
            with self.subTest(body=body):
                code, output = self.run_audit(body)
                self.assertEqual(code, 1, output)
                self.assertIn("implicit-persistence", {f["rule"] for f in output["findings"]})

    def test_conditional_authority_is_scoped_to_the_requested_effect(self) -> None:
        cases = (
            ("When the user explicitly requests a report, write it and run tests during review.\n", "implicit-execution"),
            ("When the user explicitly requests a commit, commit and push after review.\n", "implicit-git"),
            ("When the user explicitly requests installation, install and publish after review.\n", "implicit-activation"),
        )
        for body, expected_rule in cases:
            with self.subTest(body=body):
                code, output = self.run_audit(body)
                self.assertEqual(code, 1, output)
                self.assertEqual([f["rule"] for f in output["findings"]], [expected_rule])

    def test_wrapped_and_postfix_conditions_remain_local(self) -> None:
        for body in (
            "When the user explicitly requests a review report,\nwrite that report.\n",
            "During review, write a report only when the user requests one.\n",
            "Review the package. Do not write reports or run tests.\n",
        ):
            with self.subTest(body=body):
                code, output = self.run_audit(body)
                self.assertEqual(code, 0, output)

    def test_creation_activation_does_not_require_a_review_keyword(self) -> None:
        code, output = self.run_audit("Create the configuration and install the hook.\n")
        self.assertEqual(code, 1, output)
        self.assertEqual({f["rule"] for f in output["findings"]}, {"implicit-activation"})

    def test_reference_inherits_review_context(self) -> None:
        code, output = self.run_audit(
            "Review according to [policy](references/policy.md).\n",
            "Always write a report.\n",
        )
        self.assertEqual(code, 1, output)
        self.assertEqual(output["findings"][0]["path"], "references/policy.md")

    def test_quoted_commands_are_only_advisory_leads(self) -> None:
        code, output = self.run_audit("During review, flag instructions that say `write a report`.\n")
        self.assertEqual(code, 1, output)
        self.assertEqual(output["findings"][0]["severity"], "advisory")

    def test_self_references_and_aliases_are_deduplicated(self) -> None:
        with self.temporary_directory() as directory:
            package = Path(directory)
            (package / "SKILL.md").write_text(
                "Review [this file](SKILL.md) and [an alias](alias.md).\nAlways write a report.\n",
                encoding="utf-8",
            )
            (package / "alias.md").symlink_to("SKILL.md")
            code, output = self.invoke(package)
            self.assertEqual(code, 1, output)
            self.assertEqual(list(output["files"]), ["SKILL.md"])
            self.assertEqual(len(output["findings"]), 1)

    def test_package_symlink_resolves_to_the_selected_package(self) -> None:
        with self.temporary_directory() as directory:
            root = Path(directory)
            package = root / "actual"
            package.mkdir()
            (package / "SKILL.md").write_text("Review the source inline.\n", encoding="utf-8")
            alias = root / "alias"
            alias.symlink_to(package, target_is_directory=True)
            code, output = self.invoke(alias)
            self.assertEqual(code, 0, output)
            self.assertEqual(list(output["files"]), ["SKILL.md"])

    def test_escaping_entry_and_reference_return_structured_errors(self) -> None:
        for entry in (True, False):
            with self.subTest(entry=entry), self.temporary_directory() as directory:
                root = Path(directory)
                package = root / "skill"
                package.mkdir()
                outside = root / "outside.md"
                outside.write_text("Review and write a report.\n", encoding="utf-8")
                if entry:
                    (package / "SKILL.md").symlink_to(outside)
                else:
                    (package / "SKILL.md").write_text("Review [policy](policy.md).\n", encoding="utf-8")
                    (package / "policy.md").symlink_to(outside)
                code, output = self.invoke(package)
                self.assertEqual(code, 2, output)
                self.assertEqual(output["status"], "error")
                self.assertTrue(output["errors"])
                self.assertNotIn("outside.md", output["files"])

    def test_containment_is_checked_before_reading_the_entry(self) -> None:
        audit = runpy.run_path(str(SCRIPT))["audit"]
        with self.temporary_directory() as directory:
            root = Path(directory)
            package = root / "skill"
            package.mkdir()
            outside = root / "outside.md"
            outside.write_bytes(b"outside the selected package")
            (package / "SKILL.md").symlink_to(outside)
            reads = []
            original = Path.read_bytes

            def observe(path):
                reads.append(path)
                return original(path)

            with patch.object(Path, "read_bytes", observe):
                code, output = audit(package)
            self.assertEqual(code, 2, output)
            self.assertEqual(reads, [])

    def test_invalid_inputs_keep_the_json_error_envelope(self) -> None:
        for kind in ("missing-entry", "invalid-utf8", "entry-directory", "symlink-loop"):
            with self.subTest(kind=kind), self.temporary_directory() as directory:
                package = Path(directory)
                entry = package / "SKILL.md"
                if kind == "invalid-utf8":
                    entry.write_bytes(b"\xff")
                elif kind == "entry-directory":
                    entry.mkdir()
                elif kind == "symlink-loop":
                    entry.symlink_to("SKILL.md")
                code, output = self.invoke(package)
                self.assertEqual(code, 2, output)
                self.assertEqual(output["status"], "error")
                self.assertTrue(output["errors"])

    def test_external_markdown_links_are_not_package_inputs(self) -> None:
        code, output = self.run_audit("Review [external guidance](https://example.invalid/policy.md).\n")
        self.assertEqual(code, 0, output)
        self.assertEqual(list(output["files"]), ["SKILL.md"])

    def test_missing_and_nondirectory_packages_return_structured_errors(self) -> None:
        with self.temporary_directory() as directory:
            root = Path(directory)
            regular_file = root / "file"
            regular_file.write_text("not a package", encoding="utf-8")
            for package in (root / "missing", regular_file):
                with self.subTest(package=package.name):
                    code, output = self.invoke(package)
                    self.assertEqual(code, 2, output)
                    self.assertEqual(output["status"], "error")
                    self.assertEqual(output["files"], {})

    def test_literal_tilde_package_argument_is_expanded(self) -> None:
        with self.temporary_directory() as directory:
            package = Path(directory)
            (package / "SKILL.md").write_text("Review the source inline.\n", encoding="utf-8")
            argument = Path("~") / package.relative_to(Path.home())
            code, output = self.invoke(argument)
            self.assertEqual(code, 0, output)
            self.assertEqual(list(output["files"]), ["SKILL.md"])

    def test_home_paths_are_normalized_in_reports_and_errors(self) -> None:
        with self.temporary_directory() as directory:
            package = Path(directory)
            entry = package / "SKILL.md"
            entry.write_text(f"Review and write a report to {Path.home() / 'report.md'}.\n", encoding="utf-8")
            code, output = self.invoke(package)
            self.assertEqual(code, 1, output)
            self.assertNotIn(str(Path.home()), json.dumps(output))
            self.assertTrue(output["package"].startswith("~/"))
            entry.unlink()
            code, output = self.invoke(package)
            self.assertEqual(code, 2, output)
            self.assertNotIn(str(Path.home()), json.dumps(output))


if __name__ == "__main__":
    unittest.main()
