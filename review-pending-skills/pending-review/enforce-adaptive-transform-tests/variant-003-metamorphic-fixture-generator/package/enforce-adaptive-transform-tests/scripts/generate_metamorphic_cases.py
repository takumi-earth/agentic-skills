#!/usr/bin/env python3
"""Generate typed metamorphic transformation cases from one fixture model."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_ROOTS = {"schema_version", "fixture_id", "scope", "owner", "target", "unrelated", "permitted_move", "drift_state"}
REQUIRED_TARGET = {"file", "module", "node_id", "pre_state", "post_state"}


def validate_model(model: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(model, dict):
        return ["fixture must be an object"]
    missing = sorted(REQUIRED_ROOTS - model.keys())
    if missing:
        errors.append("missing fields: " + ", ".join(missing))
    if model.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    for key in ("fixture_id", "owner"):
        if not isinstance(model.get(key), str) or not model.get(key):
            errors.append(f"{key} must be a nonempty string")
    if not isinstance(model.get("scope"), list) or not model.get("scope"):
        errors.append("scope must be a nonempty array")
    target = model.get("target")
    if not isinstance(target, dict):
        errors.append("target must be an object")
    else:
        missing_target = sorted(REQUIRED_TARGET - target.keys())
        if missing_target:
            errors.append("target missing fields: " + ", ".join(missing_target))
    move = model.get("permitted_move")
    if not isinstance(move, dict) or not isinstance(move.get("file"), str) or not isinstance(move.get("module"), str):
        errors.append("permitted_move must contain file and module strings")
    if not isinstance(model.get("unrelated"), list):
        errors.append("unrelated must be an array")
    return errors


def case(
    fixture_id: str,
    variation: str,
    model: dict[str, Any],
    outcome: str,
    owner: str | None,
    changed_paths: list[str],
    preserve: list[str],
    sequence: list[str] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": f"{fixture_id}:{variation}",
        "variation": variation,
        "input": model,
        "expectation": {
            "outcome": outcome,
            "owner": owner,
            "changed_paths": changed_paths,
            "preserve": preserve,
        },
    }
    if sequence is not None:
        result["expectation"]["sequence"] = sequence
    return result


def generate(model: dict[str, Any]) -> list[dict[str, Any]]:
    fixture_id = model["fixture_id"]
    owner = model["owner"]
    original_path = model["target"]["file"]
    moved_path = model["permitted_move"]["file"]
    preserve = [item.get("node_id", "unrelated") for item in model["unrelated"]]
    cases: list[dict[str, Any]] = []

    def variant(name: str) -> dict[str, Any]:
        value = copy.deepcopy(model)
        value["variation"] = name
        return value

    for name in ("baseline", "trivia", "line-shift", "reorder"):
        value = variant(name)
        value["variation_metadata"] = {"kind": name, "semantic_change": False}
        cases.append(case(fixture_id, name, value, "applied", owner, [original_path], preserve))

    value = variant("file-move")
    value["target"]["file"] = moved_path
    cases.append(case(fixture_id, "file-move", value, "applied", owner, [moved_path], preserve))

    value = variant("module-move")
    value["target"]["file"] = moved_path
    value["target"]["module"] = model["permitted_move"]["module"]
    cases.append(case(fixture_id, "module-move", value, "applied", owner, [moved_path], preserve))

    value = variant("unrelated-extension")
    value["unrelated"].append({"node_id": "generated-unrelated-extension", "owner": "unrelated-owner", "extension": True})
    cases.append(case(fixture_id, "unrelated-extension", value, "applied", owner, [original_path], preserve + ["generated-unrelated-extension"]))

    value = variant("equal-text-decoy")
    value["unrelated"].append(
        {
            "node_id": "generated-equal-decoy",
            "owner": "unrelated-owner",
            "state": copy.deepcopy(model["target"]["pre_state"]),
        }
    )
    cases.append(case(fixture_id, "equal-text-decoy", value, "applied", owner, [original_path], preserve + ["generated-equal-decoy"]))

    value = variant("old-path-decoy")
    value["target"]["file"] = moved_path
    value["unrelated"].append(
        {
            "node_id": "generated-old-path-decoy",
            "owner": "unrelated-owner",
            "file": original_path,
            "state": copy.deepcopy(model["target"]["pre_state"]),
        }
    )
    cases.append(case(fixture_id, "old-path-decoy", value, "applied", owner, [moved_path], preserve + ["generated-old-path-decoy"]))

    value = variant("ambiguity")
    value["additional_candidates"] = [
        {"owner": owner, "node_id": "generated-second-genuine-candidate", "state": copy.deepcopy(model["target"]["pre_state"])}
    ]
    cases.append(case(fixture_id, "ambiguity", value, "ambiguous", None, [], preserve))

    value = variant("semantic-drift")
    value["target"]["pre_state"] = copy.deepcopy(model["drift_state"])
    cases.append(case(fixture_id, "semantic-drift", value, "incompatible-shape", owner, [], preserve))

    value = variant("already-applied")
    value["target"]["pre_state"] = copy.deepcopy(model["target"]["post_state"])
    cases.append(case(fixture_id, "already-applied", value, "already-applied", owner, [], preserve))

    value = variant("replay")
    cases.append(
        case(
            fixture_id,
            "replay",
            value,
            "applied-then-already-applied",
            owner,
            [original_path],
            preserve,
            ["applied", "already-applied"],
        )
    )

    value = variant("irrelevant-version")
    value["dependency_metadata"] = {"version": "999.0.0", "lockfile_changed": True, "semantic_change": False}
    cases.append(case(fixture_id, "irrelevant-version", value, "applied", owner, [original_path], preserve))
    return sorted(cases, key=lambda item: item["id"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        model = json.loads(args.fixture.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "invalid-input", "errors": [str(error)]}, sort_keys=True))
        return 2
    errors = validate_model(model)
    if errors:
        print(json.dumps({"status": "invalid", "errors": errors}, sort_keys=True))
        return 1
    output = {"schema_version": 1, "fixture_id": model["fixture_id"], "cases": generate(model)}
    rendered = json.dumps(output, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
