#!/usr/bin/env python3
"""Build inert skill-evaluation packets and validate external result ledgers."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


CASE_KINDS = {"explicit", "implicit-positive", "nearest-negative", "mixed-owner", "unauthorized-effect", "failure-polarity"}
ACTIVATION = {"triggered", "not-triggered", "ambiguous"}
EXECUTION = {"contract-satisfied", "contract-violated", "not-exercised"}


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def validate_matrix(document: Any) -> list[str]:
    if not isinstance(document, dict):
        return ["matrix must be an object"]
    errors: list[str] = []
    if document.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    skill = document.get("skill")
    if not isinstance(skill, dict):
        errors.append("skill must be an object")
    else:
        for field in ("name", "package", "sha256"):
            if not isinstance(skill.get(field), str) or not skill.get(field):
                errors.append(f"skill.{field} must be a nonempty string")
    cases = document.get("cases")
    if not isinstance(cases, list) or not cases:
        return errors + ["cases must be a nonempty array"]
    seen: set[str] = set()
    for index, case in enumerate(cases):
        prefix = f"cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{prefix} must be an object")
            continue
        identifier = case.get("id")
        if not isinstance(identifier, str) or re.fullmatch(r"[a-z0-9][a-z0-9-]*", identifier) is None:
            errors.append(f"{prefix}.id must be lowercase hyphen-case")
        elif identifier in seen:
            errors.append(f"{prefix}.id is duplicated")
        else:
            seen.add(identifier)
        if case.get("kind") not in CASE_KINDS:
            errors.append(f"{prefix}.kind is invalid")
        if not isinstance(case.get("prompt"), str) or not case.get("prompt"):
            errors.append(f"{prefix}.prompt must be a nonempty string")
        for field in ("artifacts", "allowed_effects"):
            if not isinstance(case.get(field), list) or any(not isinstance(item, str) or not item for item in case.get(field, [])):
                errors.append(f"{prefix}.{field} must be a string array")
        expectation = case.get("expectation")
        if not isinstance(expectation, dict):
            errors.append(f"{prefix}.expectation must be an object")
        else:
            if expectation.get("activation") not in ACTIVATION:
                errors.append(f"{prefix}.expectation.activation is invalid")
            if expectation.get("execution") not in EXECUTION:
                errors.append(f"{prefix}.expectation.execution is invalid")
    return errors


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build(matrix_path: Path, output: Path) -> tuple[int, dict[str, Any]]:
    try:
        matrix = load_json(matrix_path)
    except (OSError, json.JSONDecodeError) as error:
        return 2, {"status": "invalid-input", "errors": [str(error)]}
    errors = validate_matrix(matrix)
    if errors:
        return 1, {"status": "invalid", "errors": errors}
    if output.exists() and any(output.iterdir()):
        return 2, {"status": "output-not-empty", "errors": [str(output)]}
    output.mkdir(parents=True, exist_ok=True)
    packets: list[dict[str, str]] = []
    for case in sorted(matrix["cases"], key=lambda item: item["id"]):
        packet = {
            "schema_version": 1,
            "case_id": case["id"],
            "kind": case["kind"],
            "skill": matrix["skill"],
            "prompt": case["prompt"],
            "artifacts": case["artifacts"],
            "allowed_effects": case["allowed_effects"],
            "context_requirement": "fresh",
        }
        payload = canonical_bytes(packet)
        filename = f"{case['id']}.json"
        (output / filename).write_bytes(payload)
        packets.append({"case_id": case["id"], "file": filename, "sha256": hashlib.sha256(payload).hexdigest()})
    manifest = {
        "schema_version": 1,
        "matrix_sha256": hashlib.sha256(matrix_path.read_bytes()).hexdigest(),
        "packets": packets,
    }
    (output / "manifest.json").write_bytes(canonical_bytes(manifest))
    return 0, {"status": "built", "case_count": len(packets), "manifest": "manifest.json"}


def validate_results(matrix_path: Path, results_path: Path) -> tuple[int, dict[str, Any]]:
    try:
        matrix = load_json(matrix_path)
        results_document = load_json(results_path)
    except (OSError, json.JSONDecodeError) as error:
        return 2, {"status": "invalid-input", "errors": [str(error)]}
    errors = validate_matrix(matrix)
    if not isinstance(results_document, dict) or results_document.get("schema_version") != 1:
        errors.append("results schema_version must equal 1")
        results: list[Any] = []
    else:
        results_value = results_document.get("results")
        if not isinstance(results_value, list):
            errors.append("results must be an array")
            results = []
        else:
            results = results_value
    cases = {case["id"]: case for case in matrix.get("cases", []) if isinstance(case, dict) and isinstance(case.get("id"), str)}
    seen: set[str] = set()
    verdicts: list[dict[str, Any]] = []
    for index, result in enumerate(results):
        prefix = f"results[{index}]"
        if not isinstance(result, dict):
            errors.append(f"{prefix} must be an object")
            continue
        case_id = result.get("case_id")
        if case_id not in cases:
            errors.append(f"{prefix}.case_id is unknown")
            continue
        if case_id in seen:
            errors.append(f"{prefix}.case_id is duplicated")
            continue
        seen.add(case_id)
        case = cases[case_id]
        if result.get("context_mode") != "fresh":
            errors.append(f"{prefix} must use fresh context")
        if result.get("activation") not in ACTIVATION:
            errors.append(f"{prefix}.activation is invalid")
        if result.get("execution") not in EXECUTION:
            errors.append(f"{prefix}.execution is invalid")
        effects = result.get("effects")
        if not isinstance(effects, list) or any(not isinstance(item, str) for item in effects):
            errors.append(f"{prefix}.effects must be a string array")
            effects = []
        undeclared = sorted(set(effects) - set(case["allowed_effects"]))
        if undeclared:
            errors.append(f"{prefix} contains undeclared effects: {', '.join(undeclared)}")
        if not isinstance(result.get("output_locator"), str) or not result.get("output_locator"):
            errors.append(f"{prefix}.output_locator must be a nonempty string")
        if result.get("contamination") is not False:
            errors.append(f"{prefix} is contaminated or lacks contamination=false")
        if not isinstance(result.get("evaluator_rationale"), str) or not result.get("evaluator_rationale"):
            errors.append(f"{prefix}.evaluator_rationale must be a nonempty string")
        expected = case["expectation"]
        matched = result.get("activation") == expected["activation"] and result.get("execution") == expected["execution"]
        if not matched:
            errors.append(f"{prefix} verdict differs from evaluator expectation")
        verdicts.append({"case_id": case_id, "matched_expectation": matched})
    missing = sorted(set(cases) - seen)
    if missing:
        errors.append("missing results: " + ", ".join(missing))
    return (0 if not errors else 1), {
        "status": "valid" if not errors else "invalid",
        "errors": errors,
        "verdicts": sorted(verdicts, key=lambda item: item["case_id"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("matrix", type=Path)
    build_parser.add_argument("output", type=Path)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("matrix", type=Path)
    validate_parser.add_argument("results", type=Path)
    args = parser.parse_args(argv)
    if args.command == "build":
        code, result = build(args.matrix, args.output)
    else:
        code, result = validate_results(args.matrix, args.results)
    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
