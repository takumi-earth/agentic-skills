#!/usr/bin/env python3
"""Validate and render one typed guarded-mutation outcome."""

from __future__ import annotations

import argparse
import hashlib
import math
import json
import re
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
    if not isinstance(value, str) or not value.strip():
        raise OutcomeError(f"{key} must be a nonempty string")
    return value


def require_fields(value: Any, required: set[str], optional: set[str] | None = None) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise OutcomeError("field group must be an object")
    missing, unknown = required - value.keys(), value.keys() - required - (optional or set())
    if missing or unknown:
        raise OutcomeError(f"field mismatch: missing={sorted(missing)}, unknown={sorted(unknown)}")
    return value


def validate_application(payload: dict[str, Any], application: str) -> None:
    guard, desired, count, error = payload['guard'], payload['desired_state'], payload['write_count'], payload['error']
    if application == "no-op" and not (guard['matched'] and desired['proven'] and count == 0):
        raise OutcomeError("no-op requires a matched guard, proven desired state, and zero writes")
    if application == "blocked" and (guard['matched'] or count != 0):
        raise OutcomeError("blocked requires an unmatched guard and zero writes")
    if application == "write" and not (guard['matched'] and count > 0):
        raise OutcomeError("write requires a matched guard and positive write count")
    if application == "failed":
        require_text(payload, "error")
    elif error is not None:
        raise OutcomeError("a non-failed application requires error=null")


def validate(payload: Any) -> dict[str, Any]:
    """Validate the schema's exact fields and orthogonal application/verification facts."""
    require_fields(payload, {'operation','target','outcome','guard','desired_state','write_count','verification','error'}, {'application_outcome'})
    for key in ('operation', 'target'):
        require_text(payload, key)
    outcome = payload['outcome']
    if not isinstance(outcome, str) or outcome not in OUTCOMES:
        raise OutcomeError("outcome must be write, no-op, blocked, failed, or verified")
    application = payload.get('application_outcome', outcome)
    if outcome == 'verified':
        if not isinstance(application, str) or application not in OUTCOMES - {'verified'}:
            raise OutcomeError("verified requires an explicit underlying application_outcome")
    elif 'application_outcome' in payload:
        raise OutcomeError("application_outcome is only used with verified")
    guard = require_fields(payload['guard'], {'matched','condition','expected','received'})
    desired = require_fields(payload['desired_state'], {'proven','description'})
    verification = require_fields(payload['verification'], {'status','description'})
    if not isinstance(guard['matched'], bool) or not isinstance(desired['proven'], bool):
        raise OutcomeError("guard.matched and desired_state.proven must be boolean")
    require_text(guard, 'condition')
    require_text(desired, 'description')
    if not all(isinstance(guard[key], str) for key in ('expected','received')):
        raise OutcomeError("guard expected and received must be strings, including legitimate empty observations")
    count = payload['write_count']
    if isinstance(count, bool) or not isinstance(count, (int, float)) or (isinstance(count, float) and (not math.isfinite(count) or not count.is_integer())) or count < 0:
        raise OutcomeError("write_count must be a nonnegative integer")
    status = verification['status']
    if not isinstance(status, str) or status not in VERIFICATION or not isinstance(verification['description'], str):
        raise OutcomeError("verification needs a supported status and string description")
    if status != 'not-run':
        require_text(verification, 'description')
    if outcome == 'verified' and status != 'passed':
        raise OutcomeError("verified requires verification.status passed")
    if payload['error'] is not None and not isinstance(payload['error'], str):
        raise OutcomeError("error must be a string or null")
    validate_application(payload, application)
    return {**payload, 'write_count': int(count)}


def display_text(value: str) -> str:
    return re.sub(r"(?<![^\s`\"'<>(\[=:])" + re.escape(str(Path.home())) + r"(?=/|$)", "~", value)


def presentation(value: Any) -> Any:
    if isinstance(value, str):
        return display_text(value)
    if isinstance(value, dict):
        return {key: presentation(item) for key, item in value.items()}
    return value


def render(payload: dict[str, Any]) -> str:
    """Always retain actual application effects, desired-state facts, and verification."""
    guard, desired, verification = payload['guard'], payload['desired_state'], payload['verification']
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    application = payload.get('application_outcome', payload['outcome'])
    text = (f"Operation {quote(payload['operation'])} on {quote(payload['target'])}: application {application}; "
            f"completed writes: {payload['write_count']}. Guard {quote(guard['condition'])}: matched={guard['matched']}; "
            f"expected {quote(guard['expected'])}, received {quote(guard['received'])}. "
            f"Desired state {quote(desired['description'])}: proven={desired['proven']}. "
            f"Verification: {verification['status']}; {quote(verification['description'])}.")
    if payload['error'] is not None:
        text += f" Error: {quote(payload['error'])}."
    return display_text(text)


def main() -> int:
    """Load, validate, and render one outcome."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        source = arguments.input.expanduser().read_bytes()
        payload = presentation(validate(json.loads(source.decode("utf-8"))))
    except (OSError, ValueError, RuntimeError, OutcomeError) as error:
        print(f"guarded outcome render failed: {display_text(str(error))}", file=sys.stderr)
        return 2
    json.dump({"human": render(payload), "outcome": payload, "input_sha256": hashlib.sha256(source).hexdigest()}, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
