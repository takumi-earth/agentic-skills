#!/usr/bin/env python3
"""Build inert evaluation packets and check externally collected result ledgers."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


CASE_KINDS = {
    "explicit", "implicit-positive", "nearest-negative", "mixed-owner",
    "unauthorized-effect", "failure-polarity",
}
ACTIVATION = {"triggered", "not-triggered", "ambiguous"}
EXECUTION = {"contract-satisfied", "contract-violated", "not-exercised"}


def present(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace(str(Path.home()) + "/", "~/")
    if isinstance(value, list):
        return [present(item) for item in value]
    if isinstance(value, dict):
        return {key: present(item) for key, item in value.items()}
    return value


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(present(value), sort_keys=True, separators=(",", ":")) + "\n").encode()


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def member(value: Any, choices: set[str]) -> bool:
    return isinstance(value, str) and value in choices


def string_array(value: Any) -> bool:
    return isinstance(value, list) and all(nonempty(item) for item in value)


def version_one(document: dict[str, Any]) -> bool:
    return type(document.get("schema_version")) is int and document["schema_version"] == 1


def validate_matrix(document: Any) -> list[str]:
    if not isinstance(document, dict):
        return ["matrix must be an object"]
    errors: list[str] = []
    if not version_one(document):
        errors.append("schema_version must equal 1")
    skill = document.get("skill")
    if not isinstance(skill, dict):
        errors.append("skill must be an object")
    else:
        for field in ("name", "package"):
            if not nonempty(skill.get(field)):
                errors.append(f"skill.{field} must be a nonempty string")
        digest = skill.get("sha256")
        if not isinstance(digest, str) or re.fullmatch(r"[a-fA-F0-9]{64}", digest) is None:
            errors.append("skill.sha256 must be a 64-digit hexadecimal digest")
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
        if not member(case.get("kind"), CASE_KINDS):
            errors.append(f"{prefix}.kind is invalid")
        if not nonempty(case.get("prompt")):
            errors.append(f"{prefix}.prompt must be a nonempty string")
        for field in ("artifacts", "allowed_effects"):
            if not string_array(case.get(field)):
                errors.append(f"{prefix}.{field} must be a string array")
        expectation = case.get("expectation")
        if not isinstance(expectation, dict):
            errors.append(f"{prefix}.expectation must be an object")
        else:
            if not member(expectation.get("activation"), ACTIVATION):
                errors.append(f"{prefix}.expectation.activation is invalid")
            if not member(expectation.get("execution"), EXECUTION):
                errors.append(f"{prefix}.expectation.execution is invalid")
    return errors


def load_json(path: Path) -> tuple[Any, str]:
    data = path.expanduser().read_bytes()
    return json.loads(data), hashlib.sha256(data).hexdigest()


def invalid(errors: list[str]) -> tuple[int, dict[str, Any]]:
    return 2, {"status": "invalid", "ledger_valid": False, "errors": errors}


def build(matrix_path: Path, output: Path) -> tuple[int, dict[str, Any]]:
    try:
        matrix, matrix_digest = load_json(matrix_path)
    except (OSError, ValueError) as error:
        return invalid([str(error)])
    errors = validate_matrix(matrix)
    if errors:
        return invalid(errors)
    output = output.expanduser()
    try:
        if output.exists() and (not output.is_dir() or any(output.iterdir())):
            return 2, {"status": "output-not-empty", "errors": [str(output)]}
        output.mkdir(parents=True, exist_ok=True)
        workers = output / "workers"
        workers.mkdir()
        packets: list[dict[str, str]] = []
        for case in sorted(matrix["cases"], key=lambda item: item["id"]):
            packet_id = "case-" + hashlib.sha256(case["id"].encode()).hexdigest()
            packet = {
                "schema_version": 1,
                "case_id": packet_id,
                "skill": {key: matrix["skill"][key] for key in ("name", "package", "sha256")},
                "prompt": case["prompt"],
                "artifacts": case["artifacts"],
                "allowed_effects": case["allowed_effects"],
                "context_requirement": "fresh",
            }
            payload = canonical_bytes(packet)
            filename = f"workers/{packet_id}.json"
            (output / filename).write_bytes(payload)
            packets.append({
                "case_id": case["id"],
                "packet_id": packet_id,
                "file": filename,
                "sha256": hashlib.sha256(payload).hexdigest(),
            })
        manifest = {
            "schema_version": 1,
            "matrix_sha256": matrix_digest,
            "packets": packets,
        }
        (output / "manifest.json").write_bytes(canonical_bytes(manifest))
    except OSError as error:
        return 2, {"status": "incomplete-generation", "errors": [str(error)]}
    return 0, {
        "status": "built", "case_count": len(packets),
        "matrix_sha256": matrix_digest, "manifest": "manifest.json",
    }


def validate_results(matrix_path: Path, results_path: Path) -> tuple[int, dict[str, Any]]:
    try:
        matrix, matrix_digest = load_json(matrix_path)
        document, _ = load_json(results_path)
    except (OSError, ValueError) as error:
        return invalid([str(error)])
    errors = validate_matrix(matrix)
    if errors:
        return invalid(errors)
    if not isinstance(document, dict):
        return invalid(["results must be an object"])
    if not version_one(document):
        errors.append("results schema_version must equal 1")
    if document.get("matrix_sha256") != matrix_digest:
        errors.append("results must identify the evaluated matrix digest")
    results = document.get("results")
    if not isinstance(results, list):
        return invalid(errors + ["results must be an array"])
    cases = {case["id"]: case for case in matrix["cases"]}
    seen: set[str] = set()
    verdicts: list[dict[str, Any]] = []
    for index, result in enumerate(results):
        prefix = f"results[{index}]"
        if not isinstance(result, dict):
            errors.append(f"{prefix} must be an object")
            continue
        case_id = result.get("case_id")
        if not isinstance(case_id, str) or case_id not in cases:
            errors.append(f"{prefix}.case_id is unknown")
            continue
        if case_id in seen:
            errors.append(f"{prefix}.case_id is duplicated")
            continue
        seen.add(case_id)
        case = cases[case_id]
        if result.get("context_mode") != "fresh":
            errors.append(f"{prefix} must use fresh context")
        for field in ("model", "output_locator", "evaluator_rationale"):
            if not nonempty(result.get(field)):
                errors.append(f"{prefix}.{field} must be a nonempty string")
        if not member(result.get("activation"), ACTIVATION):
            errors.append(f"{prefix}.activation is invalid")
        if not member(result.get("execution"), EXECUTION):
            errors.append(f"{prefix}.execution is invalid")
        effects = result.get("effects")
        if not string_array(effects):
            errors.append(f"{prefix}.effects must be a string array")
        else:
            undeclared = sorted(set(effects) - set(case["allowed_effects"]))
            if undeclared:
                errors.append(f"{prefix} contains undeclared effects: {', '.join(undeclared)}")
        if result.get("contamination") is not False:
            errors.append(f"{prefix} is contaminated or lacks contamination=false")
        expected = case["expectation"]
        matched = (
            result.get("activation") == expected["activation"]
            and result.get("execution") == expected["execution"]
        )
        verdicts.append({"case_id": case_id, "matched_expectation": matched})
    missing = sorted(set(cases) - seen)
    if missing:
        errors.append("missing results: " + ", ".join(missing))
    if errors:
        return invalid(errors)
    matched = all(verdict["matched_expectation"] for verdict in verdicts)
    return (0 if matched else 1), {
        "status": "passed" if matched else "failed",
        "ledger_valid": True,
        "errors": [],
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
        code, report = build(args.matrix, args.output)
    else:
        code, report = validate_results(args.matrix, args.results)
    print(json.dumps(present(report), indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
