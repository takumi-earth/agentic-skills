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
HEADING = re.compile(r"^(#{1,6})\s+([A-Za-z][A-Za-z0-9-]*)\b")
DIMENSIONS = {"decision", "application", "verification"}
INFERRED_DIMENSION = {"applied": "application", "no-action": "application", "verified": "verification", "superseded-gate": "decision"}
FIELD_STATUS = re.compile(r"\b(?P<dimension>decision|application|verification)\s*(?::|=|\s)\s*(?P<state>not[- ]applied|not[- ]run|pending|blocked|running|awaiting|unverified)\b", re.IGNORECASE)
VERIFICATION_LIMIT = re.compile(r"\b(?:not[- ]run|unrun|prohibited|banned|skipped|not authorized|deliberately)\b", re.IGNORECASE)
STALE = re.compile(
    r"(?:^\s*STATUS\b.*\b(?:BLOCKED|PENDING|RUNNING)\b|"
    r"\bawait(?:ing|s)?\b.*\b(?:approval|countersignature)\b|"
    r"\bno\s+(?:remediation|application)\s+(?:is\s+|has\s+been\s+)?applied\b)",
    re.IGNORECASE,
)


class StatusError(Exception):
    """Describe malformed state or history structure."""


def _state_dimension(raw: dict[str, Any], current: str) -> str | None:
    dimension = raw.get("dimension", INFERRED_DIMENSION.get(current))
    if dimension is not None and (not isinstance(dimension, str) or dimension not in DIMENSIONS):
        raise StatusError("dimension must be decision, application, or verification")
    if current in INFERRED_DIMENSION and dimension != INFERRED_DIMENSION[current]:
        raise StatusError(f"dimension conflicts with current state: {raw['id']}")
    return dimension


def load_state(path: Path) -> dict[str, dict[str, Any]]:
    """Load terminal unit state and evidence."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_units = payload.get("units") if isinstance(payload, dict) else None
    if not isinstance(raw_units, list):
        raise StatusError("state file must contain a units array")
    units: dict[str, dict[str, Any]] = {}
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
        dimension = _state_dimension(raw, current)
        units[identifier] = {"current": current, "evidence": evidence, "dimension": dimension}
    return units


def operative_lines(text: str):
    """Yield LF-addressed current prose, excluding history and fenced examples."""
    history_depth = 0
    fence = None
    for number, line in enumerate(text.split("\n"), 1):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not line[marker.end():].strip():
                fence = None
            continue
        if fence:
            continue
        if line.strip() == BEGIN_HISTORY:
            history_depth += 1
            continue
        if line.strip() == END_HISTORY:
            history_depth -= 1
            if history_depth < 0:
                raise StatusError(f"unmatched history end marker at line {number}")
            continue
        if not history_depth:
            yield number, line
    if history_depth or fence:
        raise StatusError("unclosed history region or fenced example")


def reconcile_line(line: str, state: dict[str, Any]) -> list[dict[str, Any]]:
    """Propose only a proven dimension's status span; preserve all other text."""
    dimension = state.get("dimension", INFERRED_DIMENSION.get(state["current"]))
    fields = list(FIELD_STATUS.finditer(line))
    findings = []
    for field in fields:
        if field.group("dimension").lower() != dimension:
            continue
        if dimension == "verification" and VERIFICATION_LIMIT.search(line):
            continue
        proposed = line[:field.start("state")] + state["current"].upper() + line[field.end("state"):]
        findings.append({"classification": "dimension-status-conflict", "dimension": dimension, "proposed_line": proposed})
    if fields or STALE.search(line) is None:
        return findings
    # Unqualified STATUS/approval/application prose can contain independent limits.
    # Expose context for a human decision instead of replacing the whole line.
    return [{"classification": "needs-context", "dimension": dimension, "proposed_line": None}]


def find_stale(text: str, units: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Report dimension-specific conflicts and ambiguous legacy prose separately."""
    headings = []
    findings: list[dict[str, Any]] = []
    for line_number, line in operative_lines(text):
        heading = HEADING.match(line)
        if heading:
            level, identifier = len(heading.group(1)), heading.group(2)
            headings = [(depth, unit) for depth, unit in headings if depth < level]
            if identifier in units:
                headings.append((level, identifier))
            continue
        section = headings[-1][1] if headings else None
        state = units.get(section)
        if state is None or state["current"] not in TERMINAL:
            continue
        for finding in reconcile_line(line, state):
            findings.append({"current_line": line, "evidence": state["evidence"], "line": line_number,
                             "unit": section, **finding})
    return findings


def display_value(value: Any) -> Any:
    if isinstance(value, str):
        return re.sub(r"(?<![^\s`\"'<>(\[=:])" + re.escape(str(Path.home())) + r"(?=/|$)", "~", value)
    if isinstance(value, list):
        return [display_value(item) for item in value]
    if isinstance(value, dict):
        return {key: display_value(item) for key, item in value.items()}
    return value


def main() -> int:
    """Render the reconciliation report and fail on contradictions."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        units = load_state(arguments.state.expanduser())
        findings = find_stale(arguments.plan.expanduser().read_text(encoding="utf-8"), units)
    except (OSError, ValueError, RuntimeError, StatusError) as error:
        print(f"goal-status report failed: {display_value(str(error))}", file=sys.stderr)
        return 2
    json.dump(display_value({"findings": findings, "ok": not findings}), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
