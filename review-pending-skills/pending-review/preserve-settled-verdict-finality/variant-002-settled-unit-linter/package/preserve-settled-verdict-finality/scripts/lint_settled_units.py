#!/usr/bin/env python3
"""Detect operative reopening language for terminal decision units."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


BEGIN_HISTORY = "<!-- settled-verdict-history:begin -->"
END_HISTORY = "<!-- settled-verdict-history:end -->"
TERMINAL_STATES = {"settled", "applied", "superseded-gate"}
HEADING = re.compile(r"^#{1,6}\s+([A-Za-z][A-Za-z0-9-]*)\b")
REOPENING = re.compile(
    r"\b(?:re-?verify|re-?verification|re-?assess(?:ment)?|"
    r"renew(?:ed)?\s+countersign(?:ature)?|countersign\s+again)\b",
    re.IGNORECASE,
)


class LintError(Exception):
    """Describe an invalid ledger or document structure."""


def load_units(path: Path) -> dict[str, dict[str, Any]]:
    """Load and validate terminal units from one JSON ledger."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_units = payload.get("units") if isinstance(payload, dict) else None
    if not isinstance(raw_units, list):
        raise LintError("ledger must contain a units array")
    units: dict[str, dict[str, Any]] = {}
    for raw in raw_units:
        if not isinstance(raw, dict):
            raise LintError("every ledger unit must be an object")
        identifier = raw.get("id")
        state = raw.get("state")
        provenance = raw.get("user_provenance")
        if not isinstance(identifier, str) or not identifier:
            raise LintError("every ledger unit needs a nonempty id")
        if identifier in units:
            raise LintError(f"duplicate ledger unit: {identifier}")
        if state in TERMINAL_STATES and not isinstance(provenance, str):
            raise LintError(f"terminal unit lacks user_provenance: {identifier}")
        units[identifier] = raw
    return units


def lint_document(text: str, units: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Return reopening findings outside explicit historical regions."""

    history_depth = 0
    section: str | None = None
    findings: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if BEGIN_HISTORY in line:
            history_depth += 1
            continue
        if END_HISTORY in line:
            history_depth -= 1
            if history_depth < 0:
                raise LintError(f"unmatched history end marker at line {line_number}")
            continue
        heading = HEADING.match(line)
        if heading:
            section = heading.group(1)
        if history_depth or REOPENING.search(line) is None:
            continue
        mentioned = [identifier for identifier in units if re.search(rf"\b{re.escape(identifier)}\b", line)]
        candidates = mentioned or ([section] if section is not None else [])
        for identifier in candidates:
            unit = units.get(identifier)
            if unit is None or unit.get("state") not in TERMINAL_STATES:
                continue
            if unit.get("user_supersession"):
                continue
            findings.append(
                {
                    "line": line_number,
                    "state": unit["state"],
                    "text": line.strip(),
                    "unit": identifier,
                }
            )
    if history_depth:
        raise LintError("unclosed history region")
    return findings


def main() -> int:
    """Run the settled-unit lint and emit deterministic JSON."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--document", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        units = load_units(arguments.ledger)
        findings = lint_document(arguments.document.read_text(encoding="utf-8"), units)
    except (OSError, UnicodeError, json.JSONDecodeError, LintError) as error:
        print(f"settled-unit lint failed: {error}", file=sys.stderr)
        return 2
    json.dump({"findings": findings, "ok": not findings}, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
