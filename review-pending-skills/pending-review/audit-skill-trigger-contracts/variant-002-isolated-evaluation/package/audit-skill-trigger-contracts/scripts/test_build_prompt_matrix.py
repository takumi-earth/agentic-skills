#!/usr/bin/env python3
"""Exercise packet privacy, file integrity, and external evidence through the CLI."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("build_prompt_matrix.py")
REPO = next(parent for parent in SCRIPT.resolve().parents if (parent / "review-pending-skills").is_dir())


def matrix() -> dict:
    return {
        "schema_version": 1,
        "skill": {"name": "example-skill", "package": "skills/example-skill", "sha256": "a" * 64},
        "cases": [
            {
                "id": "implicit-positive", "kind": "implicit-positive",
                "prompt": "Review the routing in this skill.", "artifacts": ["fixtures/input.md"],
                "allowed_effects": ["read", "inline-analysis"],
                "expectation": {"activation": "triggered", "execution": "contract-satisfied"},
            },
            {
                "id": "nearest-negative", "kind": "nearest-negative",
                "prompt": "Translate this sentence into French.", "artifacts": [],
                "allowed_effects": ["read"],
                "expectation": {"activation": "not-triggered", "execution": "not-exercised"},
            },
        ],
    }


class PromptMatrixTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="matrix-test-", dir=REPO / ".scratchpad")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.matrix_path = self.root / "matrix.json"
        self.results_path = self.root / "results.json"
        self.write_matrix(matrix())

    def write_matrix(self, document: object) -> None:
        self.matrix_path.write_text(json.dumps(document), encoding="utf-8")

    def invoke(self, *arguments: object) -> tuple[int, dict]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, arguments)],
            capture_output=True, text=True, check=False, timeout=10,
        )
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def ledger(self) -> dict:
        document = json.loads(self.matrix_path.read_text())
        return {
            "schema_version": 1,
            "matrix_sha256": hashlib.sha256(self.matrix_path.read_bytes()).hexdigest(),
            "results": [
                {
                    "case_id": case["id"], "model": "fixture-model/version-1",
                    "context_mode": "fresh", **case["expectation"],
                    "effects": ["read"], "output_locator": f"results/{index}.json",
                    "contamination": False, "evaluator_rationale": "Recorded the observed entry path.",
                }
                for index, case in enumerate(document["cases"])
            ],
        }

    def validate(self, document: object) -> tuple[int, dict]:
        self.results_path.write_text(json.dumps(document), encoding="utf-8")
        return self.invoke("validate", self.matrix_path, self.results_path)

    def test_worker_packets_exclude_evaluator_identity_and_categories(self) -> None:
        output = self.root / "packets"
        code, report = self.invoke("build", self.matrix_path, output)
        self.assertEqual((code, report["status"]), (0, "built"))
        manifest = json.loads((output / "manifest.json").read_text())
        cases = {case["id"]: case for case in matrix()["cases"]}
        self.assertEqual(len(manifest["packets"]), len(cases))
        for entry in manifest["packets"]:
            packet_path = output / entry["file"]
            packet = json.loads(packet_path.read_text())
            self.assertEqual(packet_path.parent, output / "workers")
            self.assertEqual(set(packet), {
                "schema_version", "case_id", "skill", "prompt", "artifacts",
                "allowed_effects", "context_requirement",
            })
            self.assertNotIn(packet["case_id"], cases)
            self.assertEqual(packet["case_id"], entry["packet_id"])
            self.assertEqual(packet["prompt"], cases[entry["case_id"]]["prompt"])
            self.assertEqual(hashlib.sha256(packet_path.read_bytes()).hexdigest(), entry["sha256"])

    def test_manifest_named_case_keeps_its_packet_and_hash(self) -> None:
        document = matrix()
        document["cases"][0]["id"] = "manifest"
        self.write_matrix(document)
        output = self.root / "packets"
        code, _ = self.invoke("build", self.matrix_path, output)
        self.assertEqual(code, 0)
        manifest = json.loads((output / "manifest.json").read_text())
        entry = next(item for item in manifest["packets"] if item["case_id"] == "manifest")
        payload = (output / entry["file"]).read_bytes()
        self.assertEqual(json.loads(payload)["prompt"], document["cases"][0]["prompt"])
        self.assertEqual(hashlib.sha256(payload).hexdigest(), entry["sha256"])

    def test_generation_is_deterministic_and_refuses_existing_output(self) -> None:
        first, second = self.root / "first", self.root / "second"
        for output in (first, second):
            self.assertEqual(self.invoke("build", self.matrix_path, output)[0], 0)
        before = {str(path.relative_to(first)): path.read_bytes() for path in first.rglob("*.json")}
        other = {str(path.relative_to(second)): path.read_bytes() for path in second.rglob("*.json")}
        self.assertEqual(before, other)
        code, report = self.invoke("build", self.matrix_path, first)
        self.assertEqual((code, report["status"]), (2, "output-not-empty"))
        self.assertEqual(before, {str(path.relative_to(first)): path.read_bytes() for path in first.rglob("*.json")})

    def test_malformed_matrix_stops_both_commands_before_consumption(self) -> None:
        invalid_documents = [[], None, {"schema_version": 1, "cases": None}]
        for field, value in (("kind", []), ("expectation", None), ("id", [])):
            document = matrix()
            document["cases"][0][field] = value
            invalid_documents.append(document)
        duplicate = matrix()
        duplicate["cases"][1]["id"] = duplicate["cases"][0]["id"]
        invalid_documents.append(duplicate)
        for index, document in enumerate(invalid_documents):
            with self.subTest(index=index):
                self.write_matrix(document)
                output = self.root / f"invalid-{index}"
                code, report = self.invoke("build", self.matrix_path, output)
                self.assertEqual(code, 2)
                self.assertTrue(report["errors"])
                self.assertFalse(output.exists())
                code, report = self.validate({"schema_version": 1, "results": []})
                self.assertEqual((code, report["ledger_valid"]), (2, False))

    def test_valid_fresh_results_match_their_matrix(self) -> None:
        code, report = self.validate(self.ledger())
        self.assertEqual((code, report["status"], report["ledger_valid"]), (0, "passed", True))
        self.assertTrue(all(item["matched_expectation"] for item in report["verdicts"]))

    def test_behavior_failure_preserves_valid_evidence(self) -> None:
        ledger = self.ledger()
        ledger["results"][0]["execution"] = "contract-violated"
        code, report = self.validate(ledger)
        self.assertEqual((code, report["status"], report["ledger_valid"]), (1, "failed", True))
        self.assertEqual(report["errors"], [])
        self.assertFalse(report["verdicts"][0]["matched_expectation"])

    def test_contamination_undeclared_effects_and_incomplete_evidence_are_invalid(self) -> None:
        for field, value in (
            ("context_mode", "full-history"), ("contamination", True),
            ("effects", ["write"]), ("model", ""), ("case_id", []),
            ("activation", []), ("output_locator", ""),
        ):
            with self.subTest(field=field):
                ledger = self.ledger()
                ledger["results"][0][field] = value
                code, report = self.validate(ledger)
                self.assertEqual((code, report["ledger_valid"]), (2, False))
        ledger = self.ledger()
        ledger["results"].pop()
        self.assertEqual(self.validate(ledger)[0], 2)
        ledger = self.ledger()
        ledger["results"].append(copy.deepcopy(ledger["results"][0]))
        self.assertEqual(self.validate(ledger)[0], 2)

    def test_results_cannot_be_reused_after_matrix_changes(self) -> None:
        ledger = self.ledger()
        document = matrix()
        document["cases"][0]["prompt"] = "Inspect another routing example."
        self.write_matrix(document)
        code, report = self.validate(ledger)
        self.assertEqual((code, report["ledger_valid"]), (2, False))

    def test_home_paths_are_normalized_before_packet_hashing(self) -> None:
        document = matrix()
        document["skill"]["package"] = str(Path.home() / "skill-fixture")
        document["cases"][0]["artifacts"] = [str(Path.home() / "input-fixture")]
        self.write_matrix(document)
        output = self.root / "packets"
        self.assertEqual(self.invoke("build", self.matrix_path, output)[0], 0)
        manifest = json.loads((output / "manifest.json").read_text())
        for entry in manifest["packets"]:
            data = (output / entry["file"]).read_bytes()
            self.assertEqual(json.loads(data)["skill"]["package"], "~/skill-fixture")
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])


if __name__ == "__main__":
    unittest.main()
