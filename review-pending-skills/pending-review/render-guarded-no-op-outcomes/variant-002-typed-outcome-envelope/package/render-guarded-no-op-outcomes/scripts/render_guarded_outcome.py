#!/usr/bin/env python3
"""Validate and render one typed guarded-mutation outcome."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


OUTCOMES = {"write", "no-op", "blocked", "failed", "verified"}
VERIFICATION = {"not-run", "passed", "failed"}


class OutcomeError(Exception):
    """Describe an invalid guarded outcome envelope."""


def require_text(payload: dict[str, Any], key: str) -> str:
    """Return one required nonempty string."""

    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise OutcomeError(f"{key} must be a nonempty string")
    return value


def validate(payload: Any) -> dict[str, Any]:
    """Validate shared fields and outcome-specific invariants."""

    if not isinstance(payload, dict):
        raise OutcomeError("input must be a JSON object")
    operation = require_text(payload, "operation")
    target = require_text(payload, "target")
    outcome = payload.get("outcome")
    if outcome not in OUTCOMES:
        raise OutcomeError("outcome must be write, no-op, blocked, failed, or verified")
    guard = payload.get("guard")
    desired = payload.get("desired_state")
    verification = payload.get("verification")
    write_count = payload.get("write_count")
    if not isinstance(guard, dict) or not isinstance(guard.get("matched"), bool):
        raise OutcomeError("guard must be an object with boolean matched")
    for key in ("condition", "expected", "received"):
        if not isinstance(guard.get(key), str):
            raise OutcomeError(f"guard.{key} must be a string")
    if not isinstance(desired, dict) or not isinstance(desired.get("proven"), bool):
        raise OutcomeError("desired_state must be an object with boolean proven")
    if not isinstance(desired.get("description"), str) or not desired["description"]:
        raise OutcomeError("desired_state.description must be nonempty")
    if not isinstance(write_count, int) or isinstance(write_count, bool) or write_count < 0:
        raise OutcomeError("write_count must be a nonnegative integer")
    if not isinstance(verification, dict) or verification.get("status") not in VERIFICATION:
        raise OutcomeError("verification.status must be not-run, passed, or failed")
    if not isinstance(verification.get("description"), str):
        raise OutcomeError("verification.description must be a string")
    error = payload.get("error")
    if error is not None and not isinstance(error, str):
        raise OutcomeError("error must be a string or null")
    if outcome == "no-op" and not (guard["matched"] and desired["proven"] and write_count == 0):
        raise OutcomeError("no-op requires a matched guard, proven desired state, and zero writes")
    if outcome == "blocked" and not (not guard["matched"] and write_count == 0):
        raise OutcomeError("blocked requires an unmatched guard and zero writes")
    if outcome == "write" and not (guard["matched"] and write_count > 0):
        raise OutcomeError("write requires a matched guard and a positive write count")
    if outcome == "failed" and (not isinstance(error, str) or not error):
        raise OutcomeError("failed requires a nonempty error")
    if outcome == "verified" and verification["status"] != "passed":
        raise OutcomeError("verified requires verification.status passed")
    return {
        "desired_state": desired,
        "error": error,
        "guard": guard,
        "operation": operation,
        "outcome": outcome,
        "target": target,
        "verification": verification,
        "write_count": write_count,
    }


def render(payload: dict[str, Any]) -> str:
    """Render one deterministic human sentence."""

    outcome = payload["outcome"]
    guard = payload["guard"]
    target = payload["target"]
    verification = payload["verification"]
    if outcome == "no-op":
        base = (
            f"The guard for {target} matched ({guard['condition']}: expected {guard['expected']}, "
            f"received {guard['received']}), the desired state was already proven present, and the operation performed zero writes."
        )
    elif outcome == "blocked":
        base = (
            f"The operation was blocked for {target}: {guard['condition']} expected {guard['expected']} "
            f"but received {guard['received']}; zero writes were attempted."
        )
    elif outcome == "write":
        base = f"The guard for {target} matched and the operation completed {payload['write_count']} write(s)."
    elif outcome == "failed":
        base = f"The operation for {target} failed: {payload['error']}"
    else:
        base = f"Verification passed for {target}: {verification['description']}"
    if outcome != "verified":
        base += f" Verification status: {verification['status']}"
    return base


def main() -> int:
    """Load, validate, and render one outcome."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        payload = validate(json.loads(arguments.input.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError, OutcomeError) as error:
        print(f"guarded outcome render failed: {error}", file=sys.stderr)
        return 2
    json.dump({"human": render(payload), "outcome": payload}, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
