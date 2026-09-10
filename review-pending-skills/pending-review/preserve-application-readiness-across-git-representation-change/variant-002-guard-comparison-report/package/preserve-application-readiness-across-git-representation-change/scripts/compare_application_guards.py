#!/usr/bin/env python3
"""Compare guarded-application invariants and Git representation."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys
from typing import Any


REQUIRED = {
    "content_guards": dict,
    "restore_objects": dict,
    "effect_paths": list,
    "index_preservation_capability": bool,
    "head": str,
    "index_sha256": str,
    "operations": dict,
    "recovery_requirements": dict,
}


class GuardError(Exception):
    """Describe malformed guard evidence."""


def _digest(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_operations(payload: dict[str, Any]) -> None:
    effects, operations, restores = payload["effect_paths"], payload["operations"], payload["restore_objects"]
    if set(operations) != set(effects) or not set(effects).issubset(payload["content_guards"]):
        raise GuardError("every effect path requires exactly one operation and a content guard")
    identifiers = set()
    for path, operation in operations.items():
        if not isinstance(operation, dict) or set(operation) != {"id", "kind", "restore_object"}:
            raise GuardError(f"operation for {path!r} requires id, kind, and restore_object")
        identifier, kind, restore = operation["id"], operation["kind"], operation["restore_object"]
        if not _text(identifier) or identifier in identifiers:
            raise GuardError("operation ids must be nonempty and unique")
        identifiers.add(identifier)
        if kind == "delete":
            if restore is not None:
                raise GuardError("deletion has no replacement object")
        elif kind == "restore":
            if not _text(restore) or restore not in restores:
                raise GuardError(f"restore operation lacks its replacement object: {path}")
        else:
            raise GuardError(f"unsupported operation kind for {path!r}")


def validate_snapshot(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise GuardError("snapshot must be an object")
    for key, expected_type in REQUIRED.items():
        if not isinstance(payload.get(key), expected_type):
            raise GuardError(f"snapshot field {key!r} must be {expected_type.__name__}")
    effects = payload["effect_paths"]
    if not effects or not all(_text(path) for path in effects) or len(effects) != len(set(effects)):
        raise GuardError("effect_paths must contain unique nonempty paths")
    if not _text(payload["head"]) or not _digest(payload["index_sha256"]):
        raise GuardError("head must identify the snapshot and index_sha256 must be a SHA-256 digest")
    for path, digest in payload["content_guards"].items():
        if not _text(path) or (digest is not None and not _digest(digest)):
            raise GuardError("content guards require path keys and SHA-256 digests or null for absence")
    for identifier, restore in payload["restore_objects"].items():
        if not _text(identifier) or not isinstance(restore, dict) or set(restore) != {"available", "sha256"}:
            raise GuardError("restore records require an id, availability, and byte digest")
        if not isinstance(restore["available"], bool) or not _digest(restore["sha256"]):
            raise GuardError("restore availability must be boolean and sha256 a byte digest")
    recovery = payload["recovery_requirements"]
    if set(recovery) != {"method", "exact_head", "exact_index"} or not _text(recovery["method"]):
        raise GuardError("recovery_requirements requires method, exact_head, and exact_index")
    if not all(isinstance(recovery[key], bool) for key in ("exact_head", "exact_index")):
        raise GuardError("recovery identity requirements must be boolean")
    _validate_operations(payload)
    return payload


def load_snapshot(path: Path) -> dict[str, Any]:
    """Read only the supplied snapshot; do not inspect repository or object state."""
    return validate_snapshot(json.loads(path.expanduser().read_bytes().decode("utf-8")))


def compare(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Compare valid supplied claims without establishing live application authority."""
    before, after = validate_snapshot(before), validate_snapshot(after)
    representation_changes = {
        "head_changed": before["head"] != after["head"],
        "index_identity_changed": before["index_sha256"] != after["index_sha256"],
    }
    required = [operation["restore_object"] for operation in after["operations"].values() if operation["kind"] == "restore"]
    restore_bytes = lambda snapshot: {key: value["sha256"] for key, value in snapshot["restore_objects"].items()}
    recovery = after["recovery_requirements"]
    checks = {
        "content_guards_match": before["content_guards"] == after["content_guards"],
        "effect_paths_match": before["effect_paths"] == after["effect_paths"],
        "operations_match": before["operations"] == after["operations"],
        "restore_objects_match": restore_bytes(before) == restore_bytes(after),
        "current_replacements_available": all(after["restore_objects"][key]["available"] for key in required),
        "current_index_preservable": after["index_preservation_capability"],
        "recovery_contract_matches": before["recovery_requirements"] == recovery,
        "required_head_matches": not recovery["exact_head"] or not representation_changes["head_changed"],
        "required_index_matches": not recovery["exact_index"] or not representation_changes["index_identity_changed"],
    }
    blockers = [name for name, matched in checks.items() if not matched]
    return {
        "application_ready": not blockers,
        "assessment_basis": "supplied snapshot claims only",
        "independently_verified": False,
        "authorization_checked": False,
        "blockers": blockers,
        "checks": checks,
        "representation_changes": representation_changes,
        "schema_version": 1,
    }


def display_error(value: str) -> str:
    return re.sub(r"(?<![^\s`\"'<>(\[=:])" + re.escape(str(Path.home())) + r"(?=/|$)", "~", value)


def main() -> int:
    """Parse snapshots and emit the comparison report."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        report = compare(load_snapshot(arguments.before), load_snapshot(arguments.after))
    except (OSError, ValueError, RuntimeError, GuardError) as error:
        print(f"application-guard comparison failed: {display_error(str(error))}", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if report["application_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
