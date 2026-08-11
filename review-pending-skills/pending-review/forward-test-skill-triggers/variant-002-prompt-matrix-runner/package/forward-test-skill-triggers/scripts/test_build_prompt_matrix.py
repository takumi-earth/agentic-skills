#!/usr/bin/env python3
"""Direct tests for build_prompt_matrix.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("build_prompt_matrix.py")


def matrix() -> dict[str, object]:
    return {
        "schema_version": 1,
        "skill": {"name": "example-skill", "package": "skills/example-skill", "sha256": "abc123"},
        "cases": [
            {
                "id": "implicit-positive",
                "kind": "implicit-positive",
                "prompt": "Review this adaptive transform test design.",
                "artifacts": ["fixtures/design.md"],
                "allowed_effects": ["read", "inline-analysis"],
                "expectation": {"activation": "triggered", "execution": "contract-satisfied"},
            },
            {
                "id": "nearest-negative",
                "kind": "nearest-negative",
                "prompt": "Check this exact CLI output string.",
                "artifacts": [],
                "allowed_effects": ["read", "inline-analysis"],
                "expectation": {"activation": "not-triggered", "execution": "not-exercised"},
            },
        ],
    }


class PromptMatrixTest(unittest.TestCase):
    def test_build_omits_expectations_from_worker_packets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            matrix_path = root / "matrix.json"
            output = root / "packets"
            matrix_path.write_text(json.dumps(matrix()), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "build", str(matrix_path), str(output)],
                check=False,
                capture_output=True,
                text=True,
            )
            packet_text = (output / "implicit-positive.json").read_text(encoding="utf-8")
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("expectation", packet_text)
        self.assertEqual(len(manifest["packets"]), 2)

    def test_validates_complete_fresh_results(self) -> None:
        results = {
            "schema_version": 1,
            "results": [
                {
                    "case_id": "implicit-positive",
                    "context_mode": "fresh",
                    "activation": "triggered",
                    "execution": "contract-satisfied",
                    "effects": ["read", "inline-analysis"],
                    "output_locator": "results/positive.json",
                    "contamination": False,
                    "evaluator_rationale": "The skill activated and preserved its boundary.",
                },
                {
                    "case_id": "nearest-negative",
                    "context_mode": "fresh",
                    "activation": "not-triggered",
                    "execution": "not-exercised",
                    "effects": ["read"],
                    "output_locator": "results/negative.json",
                    "contamination": False,
                    "evaluator_rationale": "The exact-output owner handled the task.",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            matrix_path = root / "matrix.json"
            results_path = root / "results.json"
            matrix_path.write_text(json.dumps(matrix()), encoding="utf-8")
            results_path.write_text(json.dumps(results), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "validate", str(matrix_path), str(results_path)],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_rejects_contamination_and_undeclared_effect(self) -> None:
        results = {
            "schema_version": 1,
            "results": [
                {
                    "case_id": "implicit-positive",
                    "context_mode": "full-history",
                    "activation": "triggered",
                    "execution": "contract-satisfied",
                    "effects": ["write"],
                    "output_locator": "result.json",
                    "contamination": True,
                    "evaluator_rationale": "Inherited the diagnosis.",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            matrix_path = root / "matrix.json"
            results_path = root / "results.json"
            matrix_path.write_text(json.dumps(matrix()), encoding="utf-8")
            results_path.write_text(json.dumps(results), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "validate", str(matrix_path), str(results_path)],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("undeclared effects", result.stdout)
        self.assertIn("contaminated", result.stdout)
        self.assertIn("missing results", result.stdout)


if __name__ == "__main__":
    unittest.main()
