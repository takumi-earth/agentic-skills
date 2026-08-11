#!/usr/bin/env python3
"""Direct tests for audit_review_effects.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("audit_review_effects.py")


class ReviewSurfaceAuditorTest(unittest.TestCase):
    def run_audit(self, skill_body: str, reference: str | None = None) -> tuple[int, dict[str, object]]:
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "skill"
            package.mkdir()
            (package / "SKILL.md").write_text(skill_body, encoding="utf-8")
            if reference is not None:
                refs = package / "references"
                refs.mkdir()
                (refs / "policy.md").write_text(reference, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(package), "--json"],
                check=False,
                capture_output=True,
                text=True,
            )
        return result.returncode, json.loads(result.stdout)

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


if __name__ == "__main__":
    unittest.main()
