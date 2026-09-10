#!/usr/bin/env python3
"""Generate typed metamorphic transformation cases from one fixture model."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


REQUIRED_ROOTS = {"schema_version", "fixture_id", "scope", "owner", "target", "unrelated", "permitted_move", "drift_state"}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def source_path(value: Any) -> bool:
    return nonempty(value) and not value.startswith(("/", "~")) and "\\" not in value and ":" not in value and ".." not in value.split("/") and str(PurePosixPath(value)) == value


def validate_fields(value: Any, fields: set[str], label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    return [f"{label}.{key} must be a nonempty string" for key in sorted(fields) if not nonempty(value.get(key))]


def validate_relationships(model: dict[str, Any]) -> list[str]:
    errors = []
    target, move = model["target"], model["permitted_move"]
    for value in (target["file"], move["file"]):
        if not any(PurePosixPath(value).is_relative_to(root) and value != root for root in model["scope"]):
            errors.append(f"target path is outside declared file scope: {value}")
    if target["file"] == move["file"] or target["module"] == move["module"]:
        errors.append("file and module moves must each change their original identity")
    states = [target["pre_state"], target["post_state"], model["drift_state"]]
    keys = [json.dumps(state, sort_keys=True, allow_nan=False) for state in states]
    if len(set(keys)) != 3:
        errors.append("pre-state, post-state, and drift must be distinct")
    nodes = [target["node_id"], *(item["node_id"] for item in model["unrelated"])]
    if len(set(nodes)) != len(nodes):
        errors.append("target and unrelated node identities must be distinct")
    if any(item["owner"] == model["owner"] for item in model["unrelated"]):
        errors.append("unrelated owners must differ from the target owner")
    return errors


def validate_nested(model: dict[str, Any]) -> list[str]:
    errors = []
    for label, fields in (("target", {"file", "module", "node_id"}), ("permitted_move", {"file", "module"})):
        obj = model.get(label)
        errors += validate_fields(obj, fields, label)
        if isinstance(obj, dict) and not source_path(obj.get("file")):
            errors.append(f"{label}.file must be a normalized repository-relative path")
    target = model.get("target", {})
    for label, value in (("pre_state", target.get("pre_state") if isinstance(target, dict) else None),
                         ("post_state", target.get("post_state") if isinstance(target, dict) else None),
                         ("drift_state", model.get("drift_state"))):
        if not isinstance(value, dict) or not value:
            errors.append(f"{label} must be a nonempty object")
    unrelated = model.get("unrelated")
    if not isinstance(unrelated, list):
        errors.append("unrelated must be an array")
    else:
        for item in unrelated:
            errors += validate_fields(item, {"node_id", "owner"}, "unrelated entry")
            if isinstance(item, dict) and "file" in item and not source_path(item["file"]):
                errors.append("unrelated file must be a normalized repository-relative path")
    return errors


def validate_model(model: Any) -> list[str]:
    if not isinstance(model, dict):
        return ["fixture must be an object"]
    errors = validate_fields(model, {"fixture_id", "owner"}, "fixture")
    if set(model) != REQUIRED_ROOTS:
        errors.append("fixture fields must match the declared model")
    if type(model.get("schema_version")) is not int or model["schema_version"] != 1:
        errors.append("schema_version must be integer 1")
    scope = model.get("scope")
    if not isinstance(scope, list) or not scope or not all(source_path(p) for p in scope):
        errors.append("scope must contain normalized repository-relative paths")
    errors += validate_nested(model)
    return errors or validate_relationships(model)


def fresh_identity(prefix: str, occupied: set[str]) -> str:
    value, suffix = prefix, 0
    while value in occupied:
        suffix += 1
        value = f"{prefix}-{suffix}"
    occupied.add(value)
    return value


def display(value: str) -> str:
    return re.sub(re.escape(str(Path.home())) + r"(?=$|[/\s\x27\x22:,)])", "~", value)


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
    errors = validate_model(model)
    if errors:
        raise ValueError("; ".join(errors))
    fixture_id = model["fixture_id"]
    owner = model["owner"]
    original_path = model["target"]["file"]
    moved_path = model["permitted_move"]["file"]
    preserve = [item.get("node_id", "unrelated") for item in model["unrelated"]]
    cases: list[dict[str, Any]] = []
    occupied = {owner, model["target"]["node_id"]} | {item[k] for item in model["unrelated"] for k in ("node_id", "owner")}
    generated = {name: fresh_identity(name, occupied) for name in ("generated-unrelated-extension", "generated-equal-decoy", "generated-old-path-decoy", "generated-second-genuine-candidate", "unrelated-owner")}

    def variant(name: str) -> dict[str, Any]:
        value = copy.deepcopy(model)
        value["variation"] = name
        return value

    for name in ("baseline", "trivia", "line-shift", "reorder"):
        value = variant(name)
        value["variation_metadata"] = {"kind": name, "semantic_change": False, "adapter_materialization_required": name != "baseline"}
        cases.append(case(fixture_id, name, value, "applied", owner, [original_path], preserve))

    value = variant("file-move")
    value["target"]["file"] = moved_path
    cases.append(case(fixture_id, "file-move", value, "applied", owner, [moved_path], preserve))

    value = variant("module-move")
    value["target"]["file"] = moved_path
    value["target"]["module"] = model["permitted_move"]["module"]
    cases.append(case(fixture_id, "module-move", value, "applied", owner, [moved_path], preserve))

    value = variant("unrelated-extension")
    value["unrelated"].append({"node_id": generated["generated-unrelated-extension"], "owner": generated["unrelated-owner"], "extension": True})
    cases.append(case(fixture_id, "unrelated-extension", value, "applied", owner, [original_path], preserve + [generated["generated-unrelated-extension"]]))

    value = variant("equal-text-decoy")
    value["unrelated"].append(
        {
            "node_id": generated["generated-equal-decoy"],
            "owner": generated["unrelated-owner"],
            "state": copy.deepcopy(model["target"]["pre_state"]),
        }
    )
    cases.append(case(fixture_id, "equal-text-decoy", value, "applied", owner, [original_path], preserve + [generated["generated-equal-decoy"]]))

    value = variant("old-path-decoy")
    value["target"]["file"] = moved_path
    value["unrelated"].append(
        {
            "node_id": generated["generated-old-path-decoy"],
            "owner": generated["unrelated-owner"],
            "file": original_path,
            "state": copy.deepcopy(model["target"]["pre_state"]),
        }
    )
    cases.append(case(fixture_id, "old-path-decoy", value, "applied", owner, [moved_path], preserve + [generated["generated-old-path-decoy"]]))

    value = variant("ambiguity")
    value["additional_candidates"] = [
        {"owner": owner, "node_id": generated["generated-second-genuine-candidate"], "state": copy.deepcopy(model["target"]["pre_state"])}
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
        model = json.loads(args.fixture.expanduser().read_text(encoding="utf-8"))
        errors = validate_model(model)
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print(json.dumps({"status": "invalid-input", "errors": [display(str(error))]}, sort_keys=True))
        return 2
    if errors:
        print(json.dumps({"status": "invalid", "errors": errors}, sort_keys=True))
        return 1
    output = {"schema_version": 1, "fixture_id": model["fixture_id"], "cases": generate(model)}
    rendered = json.dumps(output, indent=2, sort_keys=True) + "\n"
    if args.output:
        try:
            args.output.expanduser().write_text(rendered, encoding="utf-8")
        except OSError as error:
            print(json.dumps({"status": "output-failure", "errors": [display(str(error))]}))
            return 2
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
