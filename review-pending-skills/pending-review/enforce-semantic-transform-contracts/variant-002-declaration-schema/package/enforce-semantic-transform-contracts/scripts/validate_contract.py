#!/usr/bin/env python3
"""Validate semantic transformation declarations without external dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "schema_version",
    "id",
    "owner",
    "scope",
    "query",
    "precondition",
    "rewrite",
    "postcondition",
    "cardinality",
    "hints",
    "outcomes",
    "transaction",
    "evidence",
}
REQUIRED_OUTCOMES = {
    "applied",
    "already-applied",
    "ambiguous",
    "mixed-state",
    "incompatible-shape",
    "postcondition-failed",
    "replay-failed",
}
REQUIRED_CASES = {
    "file-move",
    "equal-text-decoy",
    "ambiguity",
    "semantic-drift",
    "already-applied",
    "replay",
    "irrelevant-version",
}
FORBIDDEN_IDENTITY_KEYS = {
    "file",
    "file_path",
    "fixed_path",
    "full_body",
    "whole_body",
    "rendered_source",
    "source_hash",
    "fingerprint",
    "pre_fingerprint",
    "post_fingerprint",
}


def expect_object(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return {}
    return value


def expect_nonempty_strings(value: Any, path: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
        errors.append(f"{path} must be a nonempty array of nonempty strings")
        return []
    return value


def validate_contract(document: Any) -> list[str]:
    errors: list[str] = []
    root = expect_object(document, "$", errors)
    if not root:
        return errors

    missing = sorted(REQUIRED_FIELDS - root.keys())
    extra = sorted(root.keys() - REQUIRED_FIELDS)
    if missing:
        errors.append("missing fields: " + ", ".join(missing))
    if extra:
        errors.append("unknown fields: " + ", ".join(extra))
    if root.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    identifier = root.get("id")
    if not isinstance(identifier, str) or re.fullmatch(r"[a-z0-9][a-z0-9._-]+", identifier) is None:
        errors.append("id must be a stable lowercase identifier")

    owner = expect_object(root.get("owner"), "owner", errors)
    for field in ("kind", "name"):
        if not isinstance(owner.get(field), str) or not owner.get(field):
            errors.append(f"owner.{field} must be a nonempty string")

    scope = expect_object(root.get("scope"), "scope", errors)
    if scope.get("kind") not in {"workspace", "crate", "module", "owned-content"}:
        errors.append("scope.kind is invalid")
    expect_nonempty_strings(scope.get("roots"), "scope.roots", errors)

    query = expect_object(root.get("query"), "query", errors)
    for field in ("language", "semantic_identity"):
        if not isinstance(query.get(field), str) or not query.get(field):
            errors.append(f"query.{field} must be a nonempty string")
    forbidden = sorted(FORBIDDEN_IDENTITY_KEYS & query.keys())
    if forbidden:
        errors.append("query gives textual or location authority to: " + ", ".join(forbidden))

    precondition = expect_object(root.get("precondition"), "precondition", errors)
    expect_nonempty_strings(
        precondition.get("load_bearing_predicates"),
        "precondition.load_bearing_predicates",
        errors,
    )
    forbidden = sorted(FORBIDDEN_IDENTITY_KEYS & precondition.keys())
    if forbidden:
        errors.append("precondition embeds complete or textual identity: " + ", ".join(forbidden))

    rewrite = expect_object(root.get("rewrite"), "rewrite", errors)
    if not isinstance(rewrite.get("operation"), str) or not rewrite.get("operation"):
        errors.append("rewrite.operation must be a nonempty string")
    if rewrite.get("minimal_ast_change") is not True:
        errors.append("rewrite.minimal_ast_change must be true")

    postcondition = expect_object(root.get("postcondition"), "postcondition", errors)
    expect_nonempty_strings(
        postcondition.get("semantic_predicates"),
        "postcondition.semantic_predicates",
        errors,
    )

    cardinality = expect_object(root.get("cardinality"), "cardinality", errors)
    minimum = cardinality.get("minimum")
    maximum = cardinality.get("maximum")
    absence = cardinality.get("absence")
    if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 0:
        errors.append("cardinality.minimum must be a nonnegative integer")
    if not isinstance(maximum, int) or isinstance(maximum, bool) or maximum < 1:
        errors.append("cardinality.maximum must be a positive integer")
    if isinstance(minimum, int) and isinstance(maximum, int) and minimum > maximum:
        errors.append("cardinality.minimum cannot exceed maximum")
    if absence not in {"optional", "required"}:
        errors.append("cardinality.absence must be optional or required")

    hints = root.get("hints")
    if not isinstance(hints, list):
        errors.append("hints must be an array")
    else:
        for index, hint_value in enumerate(hints):
            hint = expect_object(hint_value, f"hints[{index}]", errors)
            if hint.get("authoritative") is not False:
                errors.append(f"hints[{index}].authoritative must be false")
            if hint.get("miss_behavior") != "continue-authoritative-query":
                errors.append(f"hints[{index}].miss_behavior must continue the authoritative query")
            if hint.get("kind") not in {"path", "marker", "version", "fingerprint", "hash", "rendered-fragment"}:
                errors.append(f"hints[{index}].kind is invalid")
            if not isinstance(hint.get("value"), str):
                errors.append(f"hints[{index}].value must be a string")

    outcomes = root.get("outcomes")
    if not isinstance(outcomes, list) or any(not isinstance(item, str) for item in outcomes):
        errors.append("outcomes must be an array of strings")
        outcome_set: set[str] = set()
    else:
        outcome_set = set(outcomes)
        missing_outcomes = sorted(REQUIRED_OUTCOMES - outcome_set)
        if missing_outcomes:
            errors.append("missing typed outcomes: " + ", ".join(missing_outcomes))
        expected_absence = "optional-absent" if absence == "optional" else "required-absent"
        if absence in {"optional", "required"} and expected_absence not in outcome_set:
            errors.append(f"outcomes must include {expected_absence}")

    transaction = expect_object(root.get("transaction"), "transaction", errors)
    for field in (
        "classify_complete_scope_before_edit",
        "verify_postcondition",
        "verify_replay",
        "atomic_publish",
    ):
        if transaction.get(field) is not True:
            errors.append(f"transaction.{field} must be true")

    evidence = expect_object(root.get("evidence"), "evidence", errors)
    cases = expect_nonempty_strings(evidence.get("metamorphic_cases"), "evidence.metamorphic_cases", errors)
    missing_cases = sorted(REQUIRED_CASES - set(cases))
    if cases and missing_cases:
        errors.append("missing metamorphic cases: " + ", ".join(missing_cases))
    expect_nonempty_strings(evidence.get("product_owner_tests"), "evidence.product_owner_tests", errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    args = parser.parse_args(argv)
    try:
        document = json.loads(args.contract.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "invalid-input", "errors": [str(error)]}, sort_keys=True))
        return 2
    errors = validate_contract(document)
    print(json.dumps({"status": "valid" if not errors else "invalid", "errors": errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
