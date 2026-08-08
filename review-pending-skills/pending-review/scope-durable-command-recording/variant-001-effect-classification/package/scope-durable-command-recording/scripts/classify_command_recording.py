#!/usr/bin/env python3
"""Classify whether an operation requires a durable script and report."""

from __future__ import annotations

import argparse
import json


PASSIVE = {"passive-read"}
SUBSTANTIVE = {"search-selection", "compute", "transform", "decision", "mutation", "evidence"}


def classify(operation: str) -> dict[str, object]:
    if operation in PASSIVE:
        return {
            "operation": operation,
            "durable_script_required": False,
            "condition": "operation performs computation, transformation, decision, mutation, or evidence production",
            "expected": "substantive operation",
            "received": "passive read",
            "reason": "Use a direct read command; a task-local wrapper would add indirection without replay value.",
        }
    if operation in SUBSTANTIVE:
        return {
            "operation": operation,
            "durable_script_required": True,
            "condition": "operation performs computation, transformation, decision, mutation, or evidence production",
            "expected": "durable script plus persisted report",
            "received": operation,
            "reason": "Persist exact logic, inputs, outputs, and failure conditions before relying on the result.",
        }
    return {
        "operation": operation,
        "durable_script_required": True,
        "condition": "operation classification is known",
        "expected": sorted(PASSIVE | SUBSTANTIVE),
        "received": operation,
        "reason": "Treat an unknown or mixed operation as substantive until its effects are separated.",
    }


def self_test() -> dict[str, object]:
    passive = classify("passive-read")
    search = classify("search-selection")
    mutation = classify("mutation")
    unknown = classify("mixed-pipeline")
    assert passive["durable_script_required"] is False
    assert search["durable_script_required"] is True
    assert mutation["durable_script_required"] is True
    assert unknown["durable_script_required"] is True
    return {"status": "passed", "assertions": 4}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation")
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if not arguments.self_test and arguments.operation is None:
        parser.error("--operation is required unless --self-test is used")
    return arguments


def main() -> int:
    arguments = parse_args()
    output = self_test() if arguments.self_test else classify(arguments.operation)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
