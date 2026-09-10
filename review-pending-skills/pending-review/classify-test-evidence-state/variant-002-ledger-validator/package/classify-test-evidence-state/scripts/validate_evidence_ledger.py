#!/usr/bin/env python3
"""Validate JSON test-evidence ledger states and closure claims."""

from __future__ import annotations

import argparse
from datetime import datetime
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
COMMAND_OBSERVED_STATES = STATES - {"declared", "written", "unexecuted"}
PROCESS_PASSED_STATES = {"process-passed", "focused-gate-passed", "canonical-gate-passed"}
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


def valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or ISO_8601.fullmatch(value) is None:
        return False
    zone = value[-6:]
    if zone[0] in "+-" and (int(zone[1:3]) > 23 or int(zone[4:6]) > 59):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def acceptance_errors(value: Any, prefix: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, dict) or set(value) != {"criteria", "result"}:
        return [f"{prefix}.acceptance must contain exactly criteria and result"]
    if not isinstance(value["criteria"], str) or not value["criteria"].strip():
        return [f"{prefix}.acceptance.criteria must describe the actual acceptance contract"]
    if value["result"] not in ("passed", "failed", "not-observed"):
        return [f"{prefix}.acceptance.result is invalid"]
    return []


def shape_errors(row: dict[str, Any], prefix: str) -> list[str]:
    errors = []
    missing = sorted(REQUIRED_ROW_FIELDS - row.keys())
    if missing:
        errors.append(f"{prefix} missing fields: {', '.join(missing)}")
    for field in ("id", "owner", "contract"):
        if not isinstance(row.get(field), str) or not row[field].strip():
            errors.append(f"{prefix}.{field} must be a nonempty string")
    for field in ("scope", "evidence_locator"):
        value = row.get(field)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{prefix}.{field} must be null or a nonempty string")
    state = row.get("state")
    if not isinstance(state, str) or state not in STATES:
        errors.append(f"{prefix}.state is invalid")
    if row.get("assertions") not in ("passed", "failed", "not-observed", None):
        errors.append(f"{prefix}.assertions is invalid")
    command = row.get("command")
    if command is not None and (not isinstance(command, list) or not command
            or any(not isinstance(argument, str) for argument in command) or not command[0]):
        errors.append(f"{prefix}.command needs a nonempty executable and string arguments, which may be empty")
    exit_status = row.get("exit_status")
    if exit_status is not None and (not isinstance(exit_status, int) or isinstance(exit_status, bool)):
        errors.append(f"{prefix}.exit_status must be null or an integer")
    if row.get("timestamp") is not None and not valid_timestamp(row["timestamp"]):
        errors.append(f"{prefix}.timestamp must be a valid calendar instant with timezone")
    for field in ("behavioral_closure", "canonical_scope"):
        if not isinstance(row.get(field), bool):
            errors.append(f"{prefix}.{field} must be boolean")
    return errors + acceptance_errors(row.get("acceptance"), prefix)


def observation_errors(row: dict[str, Any], prefix: str) -> list[str]:
    errors = []
    state = row["state"]
    if state in {"declared", "written", "unexecuted"}:
        if row["command"] is not None or row["exit_status"] is not None or row["assertions"] not in (None, "not-observed"):
            errors.append(f"{prefix} unexecuted state cannot carry command results")
        if row["behavioral_closure"]:
            errors.append(f"{prefix} unexecuted state cannot claim behavioral closure")
        if (row.get("acceptance") or {}).get("result") in ("passed", "failed"):
            errors.append(f"{prefix} unexecuted state cannot claim an observed acceptance result")
    if state != "declared" and not row["evidence_locator"]:
        errors.append(f"{prefix} observed or written evidence requires evidence_locator")
    if state in COMMAND_OBSERVED_STATES:
        for field in ("command", "scope", "timestamp", "evidence_locator"):
            if not row[field]:
                errors.append(f"{prefix} command-observed state requires {field}")
        if row["exit_status"] is None:
            errors.append(f"{prefix} command-observed state requires exit_status")
    if state == "compiled":
        if row["exit_status"] != 0 or row["assertions"] not in (None, "not-observed"):
            errors.append(f"{prefix} compiled requires a successful build without claiming test-body assertions")
    if state == "assertions-passed" and row["assertions"] != "passed":
        errors.append(f"{prefix} assertions-passed requires assertions=passed")
    if state in PROCESS_PASSED_STATES and row["exit_status"] != 0:
        errors.append(f"{prefix} {state} requires exit_status=0")
    return errors


def closure_errors(row: dict[str, Any], prefix: str) -> list[str]:
    errors = []
    state = row["state"]
    gate = state in {"focused-gate-passed", "canonical-gate-passed"}
    acceptance = row.get("acceptance") or {}
    if gate or row["behavioral_closure"]:
        if acceptance.get("result") != "passed":
            errors.append(f"{prefix} gate acceptance or behavioral closure requires explicit passed acceptance criteria")
        if row["assertions"] == "failed":
            errors.append(f"{prefix} a passing gate cannot report failed assertions")
    if state == "canonical-gate-passed" and not row["canonical_scope"]:
        errors.append(f"{prefix} canonical-gate-passed requires canonical_scope=true")
    if state == "focused-gate-passed" and row["canonical_scope"]:
        errors.append(f"{prefix} focused-gate-passed cannot claim canonical_scope=true")
    if row["behavioral_closure"]:
        if state not in PROCESS_PASSED_STATES or row["assertions"] != "passed" or row["exit_status"] != 0:
            errors.append(f"{prefix} behavioral closure requires process success and passed assertions")
        if not all(row[field] for field in ("command", "scope", "evidence_locator", "timestamp")):
            errors.append(f"{prefix} behavioral closure requires linked command, scope, evidence, and timestamp")
    return errors


def validate_row(row: Any, index: int) -> list[str]:
    prefix = f"rows[{index}]"
    if not isinstance(row, dict):
        return [f"{prefix} must be an object"]
    errors = shape_errors(row, prefix)
    if errors:
        return errors
    return observation_errors(row, prefix) + closure_errors(row, prefix)


def validate_ledger(document: Any) -> list[str]:
    if not isinstance(document, dict):
        return ["ledger must be an object"]
    errors: list[str] = []
    if type(document.get("schema_version")) is not int or document["schema_version"] != 1:
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


def display_error(value: str) -> str:
    return re.sub(r"(?<![^\s`\"'<>(\[=:])" + re.escape(str(Path.home())) + r"(?=/|$)", "~", value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    args = parser.parse_args(argv)
    try:
        document = json.loads(args.ledger.expanduser().read_bytes().decode("utf-8"))
    except (OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"status": "invalid-input", "errors": [display_error(str(error))]}, sort_keys=True))
        return 2
    errors = [display_error(error) for error in validate_ledger(document)]
    print(json.dumps({"status": "valid" if not errors else "invalid", "errors": errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
