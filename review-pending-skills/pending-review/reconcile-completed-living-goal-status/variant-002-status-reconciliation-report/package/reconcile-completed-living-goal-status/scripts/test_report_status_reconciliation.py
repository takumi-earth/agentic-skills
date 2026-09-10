#!/usr/bin/env python3
"""Reconcile facts without erasing independent verification and decision state."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import report_status_reconciliation as report


class StatusReportTests(unittest.TestCase):
    def setUp(self):
        self.units = {'U1': {'current': 'applied', 'evidence': 'current input application observation'}}

    def test_surgical_application_update_preserves_every_other_fact(self):
        line = 'STATUS: application: PENDING; verification: NOT RUN (prohibited); decision: settled'
        findings = report.find_stale('### U1\n' + line, self.units)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['proposed_line'], line.replace('PENDING', 'APPLIED'))
        self.assertEqual(findings[0]['dimension'], 'application')

    def test_different_dimension_and_protected_verification_do_not_change(self):
        self.assertEqual(report.find_stale('### U1\nSTATUS: verification pending', self.units), [])
        self.units['U1']['current'] = 'verified'
        for line in ('application: BLOCKED', 'verification: NOT RUN', 'verification: PENDING; execution prohibited', 'verification: PENDING (deliberately unrun)'):
            with self.subTest(line=line):
                self.assertEqual(report.find_stale('### U1\n' + line, self.units), [])

    def test_ambiguous_legacy_status_has_no_replacement(self):
        for line in ('STATUS: PENDING', 'No application has been applied; verification remains unrun'):
            with self.subTest(line=line):
                findings = report.find_stale('### U1\n' + line, self.units)
                self.assertEqual(findings[0]['classification'], 'needs-context')
                self.assertIsNone(findings[0]['proposed_line'])
                self.assertEqual(findings[0]['current_line'], line)

    def test_history_examples_and_subsection_scope(self):
        text = f'### U1\n{report.BEGIN_HISTORY}\n### Other\nSTATUS: BLOCKED\n{report.END_HISTORY}\n```text\napplication: PENDING\n```\n#### Current facts\napplication: PENDING\n### Other\napplication: PENDING'
        findings = report.find_stale(text, self.units)
        self.assertEqual([(row['unit'], row['line']) for row in findings], [('U1', 10)])
        for marker in (report.END_HISTORY, report.BEGIN_HISTORY, '```'):
            with self.subTest(marker=marker), self.assertRaises(report.StatusError):
                report.find_stale(marker, self.units)

    def test_cli_is_read_only_and_validates_evidence_dimension(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state, plan = root/'state.json', root/'plan.md'
            plan.write_text('### U1\napplication: PENDING; verification: NOT RUN')
            original = plan.read_bytes()
            value = {'id':'U1', 'current':'applied', 'dimension':'application', 'evidence':'observed'}
            state.write_text(json.dumps({'units':[value]}))
            command = [sys.executable, report.__file__, '--state', str(state), '--plan', str(plan)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)['findings'][0]['dimension'], 'application')
            self.assertEqual(plan.read_bytes(), original)
            for bad in ({'dimension':[]}, {'dimension':'verification'}, {'evidence':''}):
                state.write_text(json.dumps({'units':[{**value, **bad}]}))
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
