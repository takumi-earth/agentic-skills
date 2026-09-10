#!/usr/bin/env python3
"""Direct tests for validate_contract.py."""

from __future__ import annotations

import copy
import json
from jsonschema import Draft202012Validator
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
            "metamorphic_cases": {category: ["tests::" + category.replace("-", "_")] for category in ["file-move", "equal-text-decoy", "ambiguity", "semantic-drift", "already-applied", "replay", "irrelevant-version"]},
            "product_behavior_required": True,
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
        self.assertTrue(any("postcondition" in error["condition"] for error in output["errors"]))

    def test_rejects_authoritative_path_hint(self) -> None:
        document = valid_contract()
        document["hints"][0]["authoritative"] = True  # type: ignore[index]
        code, output = self.run_contract(document)
        self.assertEqual(code, 1)
        self.assertTrue(any("authoritative" in error["condition"] for error in output["errors"]))

    def test_rejects_whole_body_identity(self) -> None:
        document = valid_contract()
        document["query"]["whole_body"] = "fn send() {}"  # type: ignore[index]
        code, output = self.run_contract(document)
        self.assertEqual(code, 1)
        self.assertTrue(any("whole_body" in error["condition"] for error in output["errors"]))

    def test_requires_mixed_state_and_movement_evidence(self) -> None:
        document = copy.deepcopy(valid_contract())
        document["outcomes"].remove("mixed-state")  # type: ignore[union-attr]
        document["evidence"]["metamorphic_cases"]["file-move"].clear()  # type: ignore[index,union-attr]
        code, output = self.run_contract(document)
        self.assertEqual(code, 1)
        errors = json.dumps(output["errors"])
        self.assertIn("mixed-state", errors)
        self.assertIn("file-move", errors)


    def test_schema_and_cli_agree_on_structural_probes(self):
        schema = json.loads((SCRIPT.parents[1] / 'references/transformation-contract.schema.json').read_text())
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        docs = [{}, valid_contract()]
        for path, value in (
            (('schema_version',), True), (('schema_version',), 1.0),
            (('scope', 'kind'), []), (('query', 'resolver'), 4),
            (('owner', 'extra'), 'unknown'), (('transaction', 'atomic_publish'), 1),
            (('outcomes',), ['applied', 'applied']), (('outcomes',), ['other']),
            (('evidence', 'metamorphic_cases'), {'unknown': ['test']}),
        ):
            doc = valid_contract(); parent = doc
            for key in path[:-1]:
                parent = parent[key]
            parent[path[-1]] = value; docs.append(doc)
        for field in valid_contract():
            doc = valid_contract(); del doc[field]; docs.append(doc)
        for doc in docs:
            status, output = self.run_contract(doc)
            self.assertEqual(status == 0, validator.is_valid(doc), output)
            self.assertNotEqual(status, 2, output)
            for error in output['errors']:
                self.assertEqual(set(error), {'condition', 'expected', 'received'})

    def test_product_evidence_follows_actual_contract(self):
        doc = valid_contract()
        doc['evidence']['product_behavior_required'] = False
        del doc['evidence']['product_owner_tests']
        status, output = self.run_contract(doc)
        self.assertEqual(status, 0, output)
        doc['evidence']['product_behavior_required'] = True
        status, output = self.run_contract(doc)
        self.assertEqual(status, 1, output)

    def test_required_categories_and_test_identifiers_are_separate(self):
        doc = valid_contract()
        doc['evidence'] = dict(metamorphic_cases={'file-move': ['integration::relocated_owner']}, product_behavior_required=False)
        status, output = self.run_contract(doc)
        self.assertEqual(status, 0, output)
        doc['evidence']['metamorphic_cases']['file-move'] = []
        status, output = self.run_contract(doc)
        self.assertEqual(status, 1, output)

    def test_cross_field_cardinality_is_explicit(self):
        doc = valid_contract(); doc['cardinality']['minimum'] = 2
        status, output = self.run_contract(doc)
        self.assertEqual(status, 1, output)
        self.assertIn('ordered bounds', output['errors'][0]['condition'])


if __name__ == "__main__":
    unittest.main()
