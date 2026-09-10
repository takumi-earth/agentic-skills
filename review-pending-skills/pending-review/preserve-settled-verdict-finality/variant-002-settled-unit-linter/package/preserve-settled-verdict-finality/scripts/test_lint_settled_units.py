#!/usr/bin/env python3
"""Protect settled choices without confusing guard evidence with reopening."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import lint_settled_units as lint


class SettledUnitTests(unittest.TestCase):
    def setUp(self):
        self.units = {name: {"id": name, "state": "settled", "user_provenance": "actual user instruction"} for name in ("U1", "U2")}

    def test_prohibitions_and_guard_checks_preserve_decisions(self):
        for text in (
            "Do not reassess U1.", "U1 requires no re-verification.",
            "U1 reassessment is not required.", "Never require renewed countersignature for U1.",
            "Re-verify U1's hash before application.", "Reassess U1 application conditions after source drift.",
            "Re-verify the guard of U1's settled decision.",
        ):
            with self.subTest(text=text):
                self.assertEqual(lint.lint_document(text, self.units), [])

    def test_decision_requests_and_uncertainty_remain_distinct(self):
        explicit = lint.lint_document("Reassess U1's decision because a guard changed.", self.units)
        self.assertEqual(explicit[0]["classification"], "decision-reopening")
        uncertain = lint.lint_document("Re-verify U1.", self.units)
        self.assertEqual(uncertain[0]["classification"], "needs-context")
        self.assertEqual(lint.lint_document("Require renewed countersignature for U1.", self.units)[0]["classification"], "decision-reopening")

    def test_clause_scoping_and_nested_headings(self):
        text = "### U1\n#### Verification\nDo not reassess U1; reassess U2's verdict.\nRe-verify the decision.\n### Unrelated\nRe-verify the decision."
        findings = lint.lint_document(text, self.units)
        self.assertEqual([(row['unit'], row['line']) for row in findings], [('U2', 3), ('U1', 4)])

    def test_history_examples_and_supersession(self):
        text = f"### U1\n{lint.BEGIN_HISTORY}\n### U2\nReassess the decision.\n{lint.END_HISTORY}\n```text\nReassess U1.\n```\nReassess the decision."
        findings = lint.lint_document(text, self.units)
        self.assertEqual([row['unit'] for row in findings], ['U1'])
        self.units['U1']['user_supersession'] = 'later explicit user instruction'
        self.assertEqual(lint.lint_document(text, self.units), [])
        for malformed in (lint.END_HISTORY, lint.BEGIN_HISTORY, '```text'):
            with self.subTest(malformed=malformed), self.assertRaises(lint.LintError):
                lint.lint_document(malformed, self.units)

    def test_malformed_ledger_is_a_controlled_cli_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ledger, document = root/'ledger.json', root/'plan.md'
            document.write_text('Reassess U1.')
            for change in ({'state': []}, {'user_provenance': ''}, {'user_supersession': True}):
                ledger.write_text(json.dumps({'units': [{**self.units['U1'], **change}]}))
                result = subprocess.run([sys.executable, lint.__file__, '--ledger', str(ledger), '--document', str(document)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
