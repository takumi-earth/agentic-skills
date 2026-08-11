#!/usr/bin/env python3
"""Validate JSON test-evidence ledger states and closure claims."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


STATES = {
    "declared",
    "written",
    "compiled",
    "executed",
    "assertions-passed",
    "process-passed",
    "focused-gate-passed",
    "canonical-gate-passed",
    "unexecuted",
}
EXECUTED_STATES = STATES - {"declared", "written", "unexecuted"}
PROCESS_PASSED_STATES = {"process-passed", "focused-gate-passed", "canonical-gate-passed"}
ASSERTION_STATES = {"passed", "failed", "not-observed", None}
ISO_8601 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
REQUIRED_ROW_FIELDS = {
    "id",
    "owner",
    "contract",
    "state",
    "scope",
    "command",
    "assertions",
    "exit_status",
    "evidence_locator",
    "timestamp",
    "behavioral_closure",
    "canonical_scope",
}


def validate_row(row: Any, index: int) -> list[str]:
    prefix = f"rows[{index}]"
    if not isinstance(row, dict):
        return [f"{prefix} must be an object"]
    errors: list[str] = []
    missing = sorted(REQUIRED_ROW_FIELDS - row.keys())
    if missing:
        errors.append(f"{prefix} missing fields: {', '.join(missing)}")
    for field in ("id", "owner", "contract"):
        if not isinstance(row.get(field), str) or not row.get(field):
            errors.append(f"{prefix}.{field} must be a nonempty string")

    state = row.get("state")
    if state not in STATES:
        errors.append(f"{prefix}.state is invalid")
    command = row.get("command")
    if command is not None and (
        not isinstance(command, list)
        or not command
        or any(not isinstance(argument, str) or not argument for argument in command)
    ):
        errors.append(f"{prefix}.command must be null or a nonempty string array")
    scope = row.get("scope")
    if scope is not None and (not isinstance(scope, str) or not scope):
        errors.append(f"{prefix}.scope must be null or a nonempty string")
    assertions = row.get("assertions")
    if assertions not in ASSERTION_STATES:
        errors.append(f"{prefix}.assertions is invalid")
    exit_status = row.get("exit_status")
    if exit_status is not None and (not isinstance(exit_status, int) or isinstance(exit_status, bool)):
        errors.append(f"{prefix}.exit_status must be null or an integer")
    evidence = row.get("evidence_locator")
    if evidence is not None and (not isinstance(evidence, str) or not evidence):
        errors.append(f"{prefix}.evidence_locator must be null or a nonempty string")
    timestamp = row.get("timestamp")
    if timestamp is not None and (not isinstance(timestamp, str) or ISO_8601.fullmatch(timestamp) is None):
        errors.append(f"{prefix}.timestamp must be null or ISO-8601 with timezone")
    if not isinstance(row.get("behavioral_closure"), bool):
        errors.append(f"{prefix}.behavioral_closure must be boolean")
    if not isinstance(row.get("canonical_scope"), bool):
        errors.append(f"{prefix}.canonical_scope must be boolean")

    if state in {"declared", "written", "unexecuted"}:
        if command is not None or exit_status is not None or assertions not in {None, "not-observed"}:
            errors.append(f"{prefix} unexecuted state cannot carry command results")
        if row.get("behavioral_closure") is True:
            errors.append(f"{prefix} unexecuted state cannot claim behavioral closure")
    if state in EXECUTED_STATES:
        if not isinstance(command, list) or not command:
            errors.append(f"{prefix} executed state requires command identity")
        if not isinstance(scope, str) or not scope:
            errors.append(f"{prefix} executed state requires scope")
        if not isinstance(timestamp, str) or ISO_8601.fullmatch(timestamp) is None:
            errors.append(f"{prefix} executed state requires timestamp")
        if not isinstance(evidence, str) or not evidence:
            errors.append(f"{prefix} executed state requires evidence_locator")
        if exit_status is None:
            errors.append(f"{prefix} executed state requires exit_status")
    if state == "assertions-passed" and assertions != "passed":
        errors.append(f"{prefix} assertions-passed requires assertions=passed")
    if state in PROCESS_PASSED_STATES and exit_status != 0:
        errors.append(f"{prefix} {state} requires exit_status=0")
    if state == "canonical-gate-passed" and row.get("canonical_scope") is not True:
        errors.append(f"{prefix} canonical-gate-passed requires canonical_scope=true")
    if state == "focused-gate-passed" and row.get("canonical_scope") is True:
        errors.append(f"{prefix} focused-gate-passed cannot claim canonical_scope=true")

    if row.get("behavioral_closure") is True:
        if state not in PROCESS_PASSED_STATES:
            errors.append(f"{prefix} behavioral closure requires a process-passed state")
        if assertions != "passed":
            errors.append(f"{prefix} behavioral closure requires assertions=passed")
        if exit_status != 0:
            errors.append(f"{prefix} behavioral closure requires exit_status=0")
        if not command or not scope or not evidence or not timestamp:
            errors.append(f"{prefix} behavioral closure requires linked command, scope, evidence, and timestamp")
    return errors


def validate_ledger(document: Any) -> list[str]:
    if not isinstance(document, dict):
        return ["ledger must be an object"]
    errors: list[str] = []
    if document.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    rows = document.get("rows")
    if not isinstance(rows, list):
        return errors + ["rows must be an array"]
    seen: set[str] = set()
    for index, row in enumerate(rows):
        errors.extend(validate_row(row, index))
        if isinstance(row, dict) and isinstance(row.get("id"), str):
            if row["id"] in seen:
                errors.append(f"rows[{index}].id is duplicated: {row['id']}")
            seen.add(row["id"])
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    args = parser.parse_args(argv)
    try:
        document = json.loads(args.ledger.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "invalid-input", "errors": [str(error)]}, sort_keys=True))
        return 2
    errors = validate_ledger(document)
    print(json.dumps({"status": "valid" if not errors else "invalid", "errors": errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
