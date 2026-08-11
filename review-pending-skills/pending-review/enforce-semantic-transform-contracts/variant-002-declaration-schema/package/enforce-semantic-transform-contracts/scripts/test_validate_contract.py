#!/usr/bin/env python3
"""Direct tests for validate_contract.py."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("validate_contract.py")


def valid_contract() -> dict[str, object]:
    return {
        "schema_version": 1,
        "id": "client.add-timeout-hook",
        "owner": {"kind": "product", "name": "client-runtime"},
        "scope": {"kind": "crate", "roots": ["client/src"]},
        "query": {"language": "rust", "semantic_identity": "resolved Client::send method"},
        "precondition": {"load_bearing_predicates": ["resolved send call lacks timeout argument"]},
        "rewrite": {"operation": "insert captured timeout argument", "minimal_ast_change": True},
        "postcondition": {"semantic_predicates": ["resolved send call has timeout argument"]},
        "cardinality": {"minimum": 1, "maximum": 1, "absence": "required"},
        "hints": [
            {
                "kind": "path",
                "value": "client/src/client.rs",
                "authoritative": False,
                "miss_behavior": "continue-authoritative-query",
            }
        ],
        "outcomes": [
            "applied",
            "already-applied",
            "required-absent",
            "ambiguous",
            "mixed-state",
            "incompatible-shape",
            "postcondition-failed",
            "replay-failed",
        ],
        "transaction": {
            "classify_complete_scope_before_edit": True,
            "verify_postcondition": True,
            "verify_replay": True,
            "atomic_publish": True,
        },
        "evidence": {
            "metamorphic_cases": [
                "file-move",
                "equal-text-decoy",
                "ambiguity",
                "semantic-drift",
                "already-applied",
                "replay",
                "irrelevant-version",
            ],
            "product_owner_tests": ["client timeout behavior"],
        },
    }


class ContractValidatorTest(unittest.TestCase):
    def run_contract(self, document: dict[str, object]) -> tuple[int, dict[str, object]]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
        return result.returncode, json.loads(result.stdout)

    def test_accepts_complete_semantic_contract(self) -> None:
        code, output = self.run_contract(valid_contract())
        self.assertEqual(code, 0, output)
        self.assertEqual(output["status"], "valid")

    def test_rejects_missing_field(self) -> None:
        document = valid_contract()
        del document["postcondition"]
        code, output = self.run_contract(document)
        self.assertEqual(code, 1)
        self.assertTrue(any("postcondition" in error for error in output["errors"]))

    def test_rejects_authoritative_path_hint(self) -> None:
        document = valid_contract()
        document["hints"][0]["authoritative"] = True  # type: ignore[index]
        code, output = self.run_contract(document)
        self.assertEqual(code, 1)
        self.assertTrue(any("authoritative" in error for error in output["errors"]))

    def test_rejects_whole_body_identity(self) -> None:
        document = valid_contract()
        document["query"]["whole_body"] = "fn send() {}"  # type: ignore[index]
        code, output = self.run_contract(document)
        self.assertEqual(code, 1)
        self.assertTrue(any("whole_body" in error for error in output["errors"]))

    def test_requires_mixed_state_and_movement_evidence(self) -> None:
        document = copy.deepcopy(valid_contract())
        document["outcomes"].remove("mixed-state")  # type: ignore[union-attr]
        document["evidence"]["metamorphic_cases"].remove("file-move")  # type: ignore[index,union-attr]
        code, output = self.run_contract(document)
        self.assertEqual(code, 1)
        errors = "\n".join(output["errors"])
        self.assertIn("mixed-state", errors)
        self.assertIn("file-move", errors)


if __name__ == "__main__":
    unittest.main()
