#!/usr/bin/env python3
"""Direct tests for generate_metamorphic_cases.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("generate_metamorphic_cases.py")


def fixture() -> dict[str, object]:
    return {
        "schema_version": 1,
        "fixture_id": "add-timeout-hook",
        "scope": ["crate-a/src"],
        "owner": "crate-a::Client::send",
        "target": {
            "file": "crate-a/src/client.rs",
            "module": "client",
            "node_id": "send-call",
            "pre_state": {"operation": "send", "timeout": False},
            "post_state": {"operation": "send", "timeout": True},
        },
        "unrelated": [{"node_id": "decoy-send", "owner": "crate-a::Tests::send"}],
        "permitted_move": {"file": "crate-a/src/http/client.rs", "module": "http::client"},
        "drift_state": {"operation": "dispatch", "timeout": False},
    }


class MetamorphicGeneratorTest(unittest.TestCase):
    def run_generator(self, document: dict[str, object]) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
        return result.returncode, result.stdout

    def test_generates_complete_deterministic_matrix(self) -> None:
        code, first_text = self.run_generator(fixture())
        second_code, second_text = self.run_generator(fixture())
        self.assertEqual(code, 0)
        self.assertEqual(second_code, 0)
        self.assertEqual(first_text, second_text)
        output = json.loads(first_text)
        cases = {case["variation"]: case for case in output["cases"]}
        required = {
            "baseline", "trivia", "line-shift", "reorder", "file-move", "module-move",
            "unrelated-extension", "equal-text-decoy", "old-path-decoy", "ambiguity",
            "semantic-drift", "already-applied", "replay", "irrelevant-version",
        }
        self.assertEqual(set(cases), required)
        self.assertEqual(cases["file-move"]["expectation"]["changed_paths"], ["crate-a/src/http/client.rs"])
        self.assertEqual(cases["ambiguity"]["expectation"]["outcome"], "ambiguous")
        self.assertEqual(cases["ambiguity"]["expectation"]["changed_paths"], [])
        self.assertEqual(cases["replay"]["expectation"]["sequence"], ["applied", "already-applied"])

    def test_rejects_missing_move_contract(self) -> None:
        document = fixture()
        del document["permitted_move"]
        code, output = self.run_generator(document)
        self.assertEqual(code, 1)
        self.assertIn("permitted_move", output)


    def test_rejects_malformed_nested_values(self):
        for path, value in ((('unrelated',), [1]), (('target', 'file'), None), (('scope',), [42]), (('permitted_move', 'module'), ''), (('target', 'pre_state'), []), (('schema_version',), True)):
            doc = fixture(); parent = doc
            for key in path[:-1]:
                parent = parent[key]
            parent[path[-1]] = value
            status, output = self.run_generator(doc)
            self.assertEqual(status, 1, output)
            self.assertEqual(json.loads(output)['status'], 'invalid')

    def test_rejects_contradictory_variations(self):
        docs = []
        doc = fixture(); doc['permitted_move']['file'] = 'outside/client.rs'; docs.append(doc)
        doc = fixture(); doc['permitted_move']['file'] = doc['target']['file']; docs.append(doc)
        doc = fixture(); doc['permitted_move']['module'] = doc['target']['module']; docs.append(doc)
        doc = fixture(); doc['target']['post_state'] = doc['target']['pre_state']; docs.append(doc)
        doc = fixture(); doc['drift_state'] = doc['target']['pre_state']; docs.append(doc)
        doc = fixture(); doc['unrelated'][0]['node_id'] = doc['target']['node_id']; docs.append(doc)
        for doc in docs:
            status, output = self.run_generator(doc)
            self.assertEqual(status, 1, output)

    def test_generated_identities_avoid_supplied_roles(self):
        doc = fixture()
        doc['owner'] = 'unrelated-owner'
        doc['unrelated'][0]['node_id'] = 'generated-equal-decoy'
        doc['unrelated'][0]['owner'] = 'unrelated-owner-1'
        status, output = self.run_generator(doc)
        self.assertEqual(status, 0, output)
        cases = {c['variation']: c for c in json.loads(output)['cases']}
        decoy = cases['equal-text-decoy']['input']['unrelated'][-1]
        self.assertNotIn(decoy['owner'], {doc['owner'], doc['unrelated'][0]['owner']})
        self.assertNotEqual(decoy['node_id'], doc['unrelated'][0]['node_id'])
        self.assertIn(decoy['node_id'], cases['equal-text-decoy']['expectation']['preserve'])
        for name in ('trivia', 'line-shift', 'reorder'):
            self.assertTrue(cases[name]['input']['variation_metadata']['adapter_materialization_required'])


if __name__ == "__main__":
    unittest.main()
