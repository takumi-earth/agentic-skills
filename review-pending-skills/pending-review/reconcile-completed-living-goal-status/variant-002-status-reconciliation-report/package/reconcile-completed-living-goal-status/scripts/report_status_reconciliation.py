#!/usr/bin/env python3
"""Report operative stale status in a Markdown living goal."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


BEGIN_HISTORY = "<!-- goal-status-history:begin -->"
END_HISTORY = "<!-- goal-status-history:end -->"
TERMINAL = {"complete", "applied", "verified", "superseded-gate", "no-action"}
HEADING = re.compile(r"^#{1,6}\s+([A-Za-z][A-Za-z0-9-]*)\b")
STALE = re.compile(
    r"(?:^\s*STATUS\b.*\b(?:BLOCKED|PENDING|RUNNING)\b|"
    r"\bawait(?:ing|s)?\b.*\b(?:approval|countersignature)\b|"
    r"\bno\s+(?:remediation|application)\s+(?:is\s+|has\s+been\s+)?applied\b)",
    re.IGNORECASE,
)


class StatusError(Exception):
    """Describe malformed state or history structure."""


def load_state(path: Path) -> dict[str, dict[str, str]]:
    """Load terminal unit state and evidence."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_units = payload.get("units") if isinstance(payload, dict) else None
    if not isinstance(raw_units, list):
        raise StatusError("state file must contain a units array")
    units: dict[str, dict[str, str]] = {}
    for raw in raw_units:
        if not isinstance(raw, dict):
            raise StatusError("every unit must be an object")
        identifier = raw.get("id")
        current = raw.get("current")
        evidence = raw.get("evidence")
        if not all(isinstance(value, str) and value for value in (identifier, current, evidence)):
            raise StatusError("every unit needs nonempty id, current, and evidence strings")
        if identifier in units:
            raise StatusError(f"duplicate unit: {identifier}")
        units[identifier] = {"current": current, "evidence": evidence}
    return units


def find_stale(text: str, units: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    """Return stale operative lines for terminal units."""

    section: str | None = None
    history_depth = 0
    findings: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if BEGIN_HISTORY in line:
            history_depth += 1
            continue
        if END_HISTORY in line:
            history_depth -= 1
            if history_depth < 0:
                raise StatusError(f"unmatched history end marker at line {line_number}")
            continue
        heading = HEADING.match(line)
        if heading:
            section = heading.group(1)
        if history_depth or section is None or STALE.search(line) is None:
            continue
        state = units.get(section)
        if state is None or state["current"] not in TERMINAL:
            continue
        findings.append(
            {
                "current_line": line.strip(),
                "evidence": state["evidence"],
                "line": line_number,
                "proposed_line": f"STATUS: {state['current'].upper()} — {state['evidence']}",
                "unit": section,
            }
        )
    if history_depth:
        raise StatusError("unclosed history region")
    return findings


def main() -> int:
    """Render the reconciliation report and fail on contradictions."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        units = load_state(arguments.state)
        findings = find_stale(arguments.plan.read_text(encoding="utf-8"), units)
    except (OSError, UnicodeError, json.JSONDecodeError, StatusError) as error:
        print(f"goal-status report failed: {error}", file=sys.stderr)
        return 2
    json.dump({"findings": findings, "ok": not findings}, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
