#!/usr/bin/env python3
"""Compare guarded-application invariants and Git representation."""

from __future__ import annotations

import argparse
import json
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
}


class GuardError(Exception):
    """Describe malformed guard evidence."""


def load_snapshot(path: Path) -> dict[str, Any]:
    """Load and validate one evidence snapshot."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GuardError(f"snapshot must be an object: {path}")
    for key, expected_type in REQUIRED.items():
        if not isinstance(payload.get(key), expected_type):
            raise GuardError(f"snapshot field {key!r} must be {expected_type.__name__}: {path}")
    if not payload["effect_paths"] or not all(isinstance(item, str) and item for item in payload["effect_paths"]):
        raise GuardError(f"effect_paths must contain nonempty strings: {path}")
    if len(payload["effect_paths"]) != len(set(payload["effect_paths"])):
        raise GuardError(f"effect_paths contains duplicates: {path}")
    for mapping_name in ("content_guards", "restore_objects"):
        if not payload[mapping_name]:
            raise GuardError(f"{mapping_name} must not be empty: {path}")
    return payload


def compare(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Classify application invariants and representation changes."""

    checks = {
        "content_guards_match": before["content_guards"] == after["content_guards"],
        "effect_paths_match": before["effect_paths"] == after["effect_paths"],
        "restore_objects_match": before["restore_objects"] == after["restore_objects"],
        "current_index_preservable": after["index_preservation_capability"],
    }
    blockers = [name for name, matched in checks.items() if not matched]
    representation_changes = {
        "head_changed": before["head"] != after["head"],
        "index_identity_changed": before["index_sha256"] != after["index_sha256"],
    }
    return {
        "application_ready": not blockers,
        "blockers": blockers,
        "checks": checks,
        "representation_changes": representation_changes,
        "schema_version": 1,
    }


def main() -> int:
    """Parse snapshots and emit the comparison report."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        report = compare(load_snapshot(arguments.before), load_snapshot(arguments.after))
    except (OSError, UnicodeError, json.JSONDecodeError, GuardError) as error:
        print(f"application-guard comparison failed: {error}", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if report["application_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
