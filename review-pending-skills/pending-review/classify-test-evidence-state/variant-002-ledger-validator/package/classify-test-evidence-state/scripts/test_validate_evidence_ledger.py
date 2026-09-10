#!/usr/bin/env python3
"""Direct tests for validate_evidence_ledger.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import validate_evidence_ledger as validator


SCRIPT = Path(__file__).with_name("validate_evidence_ledger.py")


def row(**updates: object) -> dict[str, object]:
    value: dict[str, object] = {
        "id": "behavior-a",
        "owner": "client-runtime",
        "contract": "cancellation propagates",
        "state": "unexecuted",
        "scope": None,
        "command": None,
        "assertions": "not-observed",
        "exit_status": None,
        "evidence_locator": "tests/client.rs:42",
        "timestamp": None,
        "behavioral_closure": False,
        "canonical_scope": False,
    }
    value.update(updates)
    return value


class EvidenceLedgerTest(unittest.TestCase):
    def run_ledger(self, rows: list[dict[str, object]]) -> tuple[int, dict[str, object]]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            path.write_text(json.dumps({"schema_version": 1, "rows": rows}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
        return result.returncode, json.loads(result.stdout)

    def test_accepts_honest_unexecuted_source(self) -> None:
        code, output = self.run_ledger([row()])
        self.assertEqual(code, 0, output)

    def test_preserves_assertion_pass_process_fail_without_closure(self) -> None:
        code, output = self.run_ledger(
            [
                row(
                    state="assertions-passed",
                    scope="focused client test",
                    command=["cargo", "test", "client"],
                    assertions="passed",
                    exit_status=1,
                    evidence_locator="logs/client-test.json",
                    timestamp="2026-08-12T00:00:00Z",
                )
            ]
        )
        self.assertEqual(code, 0, output)

    def test_rejects_written_behavioral_closure(self) -> None:
        code, output = self.run_ledger([row(state="written", behavioral_closure=True)])
        self.assertEqual(code, 1)
        self.assertTrue(any("behavioral closure" in error for error in output["errors"]))

    def test_distinguishes_focused_and_canonical_passes(self) -> None:
        focused = row(
            id="focused",
            state="focused-gate-passed",
            scope="client package",
            command=["cargo", "test", "-p", "client"],
            assertions="passed",
            exit_status=0,
            evidence_locator="logs/focused.json",
            timestamp="2026-08-12T00:01:00Z",
            behavioral_closure=True,
            acceptance={"criteria": "focused client assertions and successful process", "result": "passed"},
        )
        canonical = row(
            id="canonical",
            state="canonical-gate-passed",
            scope="workspace canonical gate",
            command=["just", "ci"],
            assertions="passed",
            exit_status=0,
            evidence_locator="logs/canonical.json",
            timestamp="2026-08-12T00:02:00Z",
            behavioral_closure=True,
            canonical_scope=True,
            acceptance={"criteria": "all required workspace checks pass", "result": "passed"},
        )
        code, output = self.run_ledger([focused, canonical])
        self.assertEqual(code, 0, output)
        canonical["canonical_scope"] = False
        code, output = self.run_ledger([focused, canonical])
        self.assertEqual(code, 1)
        self.assertTrue(any("canonical_scope" in error for error in output["errors"]))

    def test_malformed_values_calendar_dates_and_boolean_version_are_rejected(self):
        for changes in ({'state': []}, {'assertions': {}}, {'timestamp': '2026-02-30T00:00:00Z'},
                        {'timestamp': '2026-01-01T00:00:00+01:99'}, {'acceptance': {'criteria':'gate', 'result':[]}}):
            with self.subTest(changes=changes):
                code, output = self.run_ledger([row(**changes)])
                self.assertEqual(code, 1, output)
        self.assertTrue(validator.validate_ledger({'schema_version': True, 'rows': []}))

    def test_written_evidence_needs_a_locator_but_declaration_does_not(self):
        self.assertEqual(self.run_ledger([row(state='written', evidence_locator=None)])[0], 1)
        self.assertEqual(self.run_ledger([row(state='declared', evidence_locator=None)])[0], 0)

    def test_exact_empty_argument_and_compilation_observation(self):
        compiled = row(state='compiled', command=['compiler', '', 'input.rs'], scope='build only', exit_status=0,
                       timestamp='2024-02-29T12:00:00+08:00')
        self.assertEqual(self.run_ledger([compiled])[0], 0)
        self.assertEqual(compiled['command'][1], '')
        self.assertEqual(self.run_ledger([{**compiled, 'assertions':'passed'}])[0], 1)
        self.assertEqual(self.run_ledger([{**compiled, 'command':['', 'arg']}])[0], 1)

    def test_gate_acceptance_is_not_inferred_from_process_success(self):
        gate = row(state='canonical-gate-passed', scope='canonical', command=['runner'], exit_status=0,
                   timestamp='2026-08-12T00:00:00Z', canonical_scope=True, assertions='failed')
        self.assertEqual(self.run_ledger([gate])[0], 1)
        gate['acceptance'] = {'criteria':'build and assertion contract', 'result':'passed'}
        self.assertEqual(self.run_ledger([gate])[0], 1)
        gate['assertions'] = 'not-observed'
        gate['acceptance'] = {'criteria':'compile-only canonical gate', 'result':'passed'}
        self.assertEqual(self.run_ledger([gate])[0], 0)
        gate['behavioral_closure'] = True
        self.assertEqual(self.run_ledger([gate])[0], 1)

    def test_invalid_bytes_nesting_and_missing_paths_keep_json_failures(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'input.json'
            for data in (b'\xff', b'['*1500 + b'0' + b']'*1500):
                path.write_bytes(data)
                result = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
                self.assertIn(result.returncode, (1, 2))
                self.assertIn(json.loads(result.stdout)['status'], ('invalid', 'invalid-input'))
                self.assertEqual(result.stderr, '')
            missing = Path.home()/Path(temporary).name/'missing.json'
            result = subprocess.run([sys.executable, str(SCRIPT), str(missing)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('~/', result.stdout)
            self.assertNotIn(str(Path.home())+'/', result.stdout)


if __name__ == "__main__":
    unittest.main()
