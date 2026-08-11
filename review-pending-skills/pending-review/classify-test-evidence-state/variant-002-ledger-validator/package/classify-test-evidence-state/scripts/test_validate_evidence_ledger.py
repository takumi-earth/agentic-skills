#!/usr/bin/env python3
"""Direct tests for validate_evidence_ledger.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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
        )
        code, output = self.run_ledger([focused, canonical])
        self.assertEqual(code, 0, output)
        canonical["canonical_scope"] = False
        code, output = self.run_ledger([focused, canonical])
        self.assertEqual(code, 1)
        self.assertTrue(any("canonical_scope" in error for error in output["errors"]))


if __name__ == "__main__":
    unittest.main()
