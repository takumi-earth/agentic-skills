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
HEADING = re.compile(r"^(#{1,6})\s+([A-Za-z][A-Za-z0-9-]*)\b")
REOPENING = re.compile(
    r"\b(?:re-?verify|re-?verification|re-?assess(?:ment)?|"
    r"renew(?:ed)?\s+countersign(?:ature)?|countersign\s+again)\b",
    re.IGNORECASE,
)
PROHIBITION = re.compile(r"\b(?:do not|does not|must not|shall not|should not|don't|never|no|without|prohibit(?:ed)?|forbid(?:den)?)\b[^;.!?]*$", re.IGNORECASE)
GUARD = re.compile(r"\b(?:guards?|hash(?:es)?|inputs?|preconditions?|application (?:conditions?|readiness)|worktree|repository state|source|configuration)\b", re.IGNORECASE)
DECISION = re.compile(r"\b(?:decision|verdict|selection|approval|countersign(?:ature)?)\b", re.IGNORECASE)


class LintError(Exception):
    """Describe an invalid ledger or document structure."""


def _validate_unit(raw: Any) -> str:
    if not isinstance(raw, dict):
        raise LintError("every ledger unit must be an object")
    identifier, state, provenance = raw.get("id"), raw.get("state"), raw.get("user_provenance")
    if not isinstance(identifier, str) or not identifier:
        raise LintError("every ledger unit needs a nonempty id")
    if not isinstance(state, str):
        raise LintError(f"unit state must be a string: {identifier}")
    if state in TERMINAL_STATES and (not isinstance(provenance, str) or not provenance.strip()):
        raise LintError(f"terminal unit lacks user_provenance: {identifier}")
    supersession = raw.get("user_supersession")
    if supersession is not None and (not isinstance(supersession, str) or not supersession.strip()):
        raise LintError(f"user_supersession must be null or nonempty user evidence: {identifier}")
    return identifier


def load_units(path: Path) -> dict[str, dict[str, Any]]:
    """Load and validate terminal units from one JSON ledger."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_units = payload.get("units") if isinstance(payload, dict) else None
    if not isinstance(raw_units, list):
        raise LintError("ledger must contain a units array")
    units: dict[str, dict[str, Any]] = {}
    for raw in raw_units:
        identifier = _validate_unit(raw)
        if identifier in units:
            raise LintError(f"duplicate ledger unit: {identifier}")
        units[identifier] = raw
    return units


def operative_lines(text: str):
    """Exclude history and fenced examples without changing surrounding heading scope."""
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
                raise LintError(f"unmatched history end marker at line {number}")
            continue
        if not history_depth:
            yield number, line
    if history_depth or fence:
        raise LintError("unclosed history region or fenced example")


def reopening_kind(clause: str, match: re.Match[str]) -> str | None:
    if PROHIBITION.search(clause[:match.start()]):
        return None
    following = re.split(r"\b(?:if|because|after|when)\b", clause[match.end():], maxsplit=1, flags=re.IGNORECASE)[0]
    if re.match(r"\s+(?:is|remains|must be)\s+(?:not (?:needed|required|allowed)|forbidden|prohibited|unnecessary)\b", following, re.IGNORECASE):
        return None
    guard = GUARD.search(following)
    decision = DECISION.search(following)
    if guard and (not decision or guard.start() < decision.start()):
        return None
    if decision or "countersign" in match.group().lower():
        return "decision-reopening"
    return "needs-context"


def _line_findings(line: str, section: str | None, units: dict[str, dict[str, Any]]):
    for clause in re.split(r"[;.!?]|\bbut\b|\bhowever\b", line, flags=re.IGNORECASE):
        match = REOPENING.search(clause)
        classification = reopening_kind(clause, match) if match else None
        if classification is None:
            continue
        mentioned = [identifier for identifier in units if re.search(rf"\b{re.escape(identifier)}\b", clause)]
        for identifier in mentioned or ([section] if section else []):
            unit = units[identifier]
            if unit.get("state") in TERMINAL_STATES and not unit.get("user_supersession"):
                yield {"state": unit["state"], "text": clause.strip(), "unit": identifier, "classification": classification}


def lint_document(text: str, units: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Return advisory decision or uncertain-action findings, not a semantic verdict."""
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
        findings.extend({"line": line_number, **finding} for finding in _line_findings(line, section, units))
    return findings


def display_text(value: str) -> str:
    return re.sub(r"(?<![^\s`\"'<>(\[=:])" + re.escape(str(Path.home())) + r"(?=/|$)", "~", value)


def main() -> int:
    """Run the settled-unit lint and emit deterministic JSON."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--document", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        units = load_units(arguments.ledger.expanduser())
        findings = lint_document(arguments.document.expanduser().read_text(encoding="utf-8"), units)
    except (OSError, ValueError, RuntimeError, LintError) as error:
        message = display_text(str(error))
        print(f"settled-unit lint failed: {message}", file=sys.stderr)
        return 2
    for finding in findings:
        finding["text"] = display_text(finding["text"])
    json.dump({"findings": findings, "ok": not findings, "coverage": "bounded English lexical signals; not semantic proof"}, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
