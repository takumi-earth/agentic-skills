#!/usr/bin/env python3
"""Validate that an architectural-regression packet is decision-ready."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


SCHEMA_VERSION = 1
FINDING_HEADING = re.compile(r"^## Finding `(?P<id>[^`]+)`:")
SUBSECTION_HEADING = re.compile(r"^### (?P<title>.+)$")
VERDICT_UNIT_HEADING = re.compile(r"^#### `(?P<id>[^`]+)`(?:\s|$)")
SOURCE_LOCATOR = re.compile(r"`(?:[^`:\s]+:)*(?:[^`:\s]+/)*[^`:\s]+:\d+(?:-\d+)?`")
UNRESOLVED_MARKER = re.compile(r"_{4,}|\b(?:TODO|TBD|TKTK)\b", re.IGNORECASE)
REQUIRED_UNIT_LABELS = ("Evidence", "Change", "Approval means", "Rejection means", "User verdict", "User comment")


class PacketError(Exception):
    """Raised when packet inputs are malformed."""


def require_mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PacketError(f"{label} must be an object")
    return value


def require_list(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise PacketError(f"{label} must be an array")
    return value


def require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise PacketError(f"{label} must be a non-empty string")
    return value


def require_nonnegative_int(value: object, label: str, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise PacketError(f"{label} must be a non-negative integer")
    return value


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PacketError(f"failed to read {label}: {error}") from error
    return require_mapping(value, label)


def markdown_fence(line: str) -> str | None:
    match = re.match(r"^\s*(`{3,}|~{3,})", line)
    return match.group(1)[0] if match else None


def hardwrapped_lines(lines: list[str]) -> list[int]:
    violations: list[int] = []
    fence_character: str | None = None
    frontmatter = bool(lines and lines[0] == "---")
    previous_nonblank = False
    for index, line in enumerate(lines, start=1):
        if frontmatter:
            if index > 1 and line == "---":
                frontmatter = False
            continue
        fence = markdown_fence(line)
        if fence is not None:
            if fence_character is None:
                fence_character = fence
            elif fence == fence_character:
                fence_character = None
            previous_nonblank = True
            continue
        if fence_character is not None:
            continue
        heading = bool(re.match(r"^#{1,6} ", line))
        table = line.startswith("|")
        unordered = bool(re.match(r"^\s*[-+*]\s+", line))
        ordered = bool(re.match(r"^\s*\d+\.\s+", line))
        quote = line.startswith(">")
        thematic = bool(re.match(r"^ {0,3}(?:-{3,}|\*{3,}|_{3,})\s*$", line))
        html_comment = line.startswith("<!--") or line.endswith("-->")
        ordinary = bool(line) and not any((heading, table, unordered, ordered, quote, thematic, html_comment))
        if ordinary and previous_nonblank:
            violations.append(index)
        previous_nonblank = bool(line)
    return violations


def finding_blocks(lines: list[str]) -> dict[str, tuple[int, int]]:
    starts: list[tuple[str, int]] = []
    for index, line in enumerate(lines):
        match = FINDING_HEADING.match(line)
        if match:
            starts.append((match.group("id"), index))
    blocks: dict[str, tuple[int, int]] = {}
    for position, (finding_id, start) in enumerate(starts):
        end = starts[position + 1][1] if position + 1 < len(starts) else len(lines)
        if finding_id in blocks:
            raise PacketError(f"duplicate finding heading: {finding_id}")
        blocks[finding_id] = (start, end)
    return blocks


def verdict_units(block_lines: list[str]) -> list[tuple[str, list[str]]]:
    starts: list[tuple[str, int]] = []
    for index, line in enumerate(block_lines):
        match = VERDICT_UNIT_HEADING.match(line)
        if match:
            starts.append((match.group("id"), index))
    units: list[tuple[str, list[str]]] = []
    for position, (unit_id, start) in enumerate(starts):
        end = starts[position + 1][1] if position + 1 < len(starts) else len(block_lines)
        units.append((unit_id, block_lines[start:end]))
    return units


def verdict_unit_field(unit_lines: list[str], label: str) -> tuple[bool, str]:
    prefix = f"**{label}:**"
    positions = [index for index, line in enumerate(unit_lines) if line.startswith(prefix)]
    if not positions:
        return False, ""
    start = positions[0]
    values = [unit_lines[start][len(prefix) :].strip()]
    for line in unit_lines[start + 1 :]:
        if any(line.startswith(f"**{candidate}:**") for candidate in REQUIRED_UNIT_LABELS):
            break
        if re.match(r"^#{1,6}\s", line):
            break
        values.append(line.strip())
    return True, "\n".join(value for value in values if value).strip()


def evidence_queries_by_id(evidence: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if evidence.get("schema_version") != SCHEMA_VERSION:
        raise PacketError(f"evidence schema_version must be {SCHEMA_VERSION}")
    queries: dict[str, dict[str, Any]] = {}
    for index, raw_query in enumerate(require_list(evidence.get("queries"), "evidence.queries")):
        query = require_mapping(raw_query, f"evidence.queries[{index}]")
        query_id = require_string(query.get("id"), f"evidence.queries[{index}].id")
        if query_id in queries:
            raise PacketError(f"duplicate evidence query id: {query_id}")
        queries[query_id] = query
    return queries


def call_inventory_records(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    if inventory.get("schema_version") != SCHEMA_VERSION:
        raise PacketError(f"Rust call inventory schema_version must be {SCHEMA_VERSION}")
    records: list[dict[str, Any]] = []
    site_keys: set[str] = set()
    owners: set[str] = set()
    for index, raw_record in enumerate(require_list(inventory.get("calls"), "Rust call inventory.calls")):
        record = require_mapping(raw_record, f"Rust call inventory.calls[{index}]")
        owner = require_string(record.get("owner"), f"Rust call inventory.calls[{index}].owner")
        site_key = require_string(record.get("site_key"), f"Rust call inventory.calls[{index}].site_key")
        if site_key in site_keys:
            raise PacketError(f"duplicate Rust call inventory site_key: {site_key}")
        site_keys.add(site_key)
        owners.add(owner)
        records.append(record)
    if inventory.get("call_count") != len(records):
        raise PacketError(f"Rust call inventory call_count is {inventory.get('call_count')!r}; computed {len(records)}")
    if inventory.get("owner_count") != len(owners):
        raise PacketError(f"Rust call inventory owner_count is {inventory.get('owner_count')!r}; computed {len(owners)}")
    return records


def validate(
    packet: str,
    contract: dict[str, Any],
    available_queries: set[str] | dict[str, dict[str, Any]],
    rust_call_inventory: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION:
        raise PacketError(f"contract schema_version must be {SCHEMA_VERSION}")
    lines = packet.splitlines()
    if contract.get("require_unwrapped_prose", True):
        wrapped = hardwrapped_lines(lines)
        if wrapped:
            errors.append("manual prose wrapping detected at lines: " + ", ".join(str(line) for line in wrapped))
    blocks = finding_blocks(lines)
    raw_findings = require_list(contract.get("findings"), "findings")
    if not raw_findings:
        raise PacketError("contract findings must not be empty")
    contracted_ids: list[str] = []
    for index, raw_finding in enumerate(raw_findings):
        finding = require_mapping(raw_finding, f"findings[{index}]")
        finding_id = require_string(finding.get("id"), f"findings[{index}].id")
        if finding_id in contracted_ids:
            raise PacketError(f"duplicate contract finding id: {finding_id}")
        contracted_ids.append(finding_id)
    for finding_id, bounds in blocks.items():
        block = "\n".join(lines[bounds[0] : bounds[1]])
        if finding_id not in contracted_ids:
            errors.append(f"uncontracted finding heading: {finding_id}")
        if UNRESOLVED_MARKER.search(block):
            errors.append(f"finding {finding_id} contains an unresolved placeholder marker")
    global_forbidden = [
        require_string(value, f"forbidden_phrases[{index}]")
        for index, value in enumerate(require_list(contract.get("forbidden_phrases", []), "forbidden_phrases"))
    ]
    for phrase in global_forbidden:
        if phrase.casefold() in packet.casefold():
            errors.append(f"packet contains forbidden deferral: {phrase!r}")
    for index, raw_finding in enumerate(raw_findings):
        finding = require_mapping(raw_finding, f"findings[{index}]")
        finding_id = require_string(finding.get("id"), f"findings[{index}].id")
        bounds = blocks.get(finding_id)
        if bounds is None:
            errors.append(f"missing finding heading: {finding_id}")
            continue
        block_lines = lines[bounds[0] : bounds[1]]
        block = "\n".join(block_lines)
        subsection_titles = {match.group("title") for line in block_lines if (match := SUBSECTION_HEADING.match(line))}
        for section_index, raw_section in enumerate(require_list(finding.get("required_sections", []), f"finding {finding_id}.required_sections")):
            section = require_string(raw_section, f"finding {finding_id}.required_sections[{section_index}]")
            if section not in subsection_titles:
                errors.append(f"finding {finding_id} is missing subsection: {section}")
        for string_index, raw_string in enumerate(require_list(finding.get("required_strings", []), f"finding {finding_id}.required_strings")):
            required = require_string(raw_string, f"finding {finding_id}.required_strings[{string_index}]")
            if required not in block:
                errors.append(f"finding {finding_id} is missing required text: {required!r}")
        required_queries = [
            require_string(value, f"finding {finding_id}.required_evidence_queries[{query_index}]")
            for query_index, value in enumerate(require_list(finding.get("required_evidence_queries", []), f"finding {finding_id}.required_evidence_queries"))
        ]
        available_query_ids = set(available_queries)
        for query_id in required_queries:
            if query_id not in available_query_ids:
                errors.append(f"finding {finding_id} requires unavailable evidence query: {query_id}")
            if f"`{query_id}`" not in block:
                errors.append(f"finding {finding_id} does not cite evidence query: {query_id}")
        evidence_assertions = require_list(finding.get("evidence_assertions", []), f"finding {finding_id}.evidence_assertions")
        for assertion_index, raw_assertion in enumerate(evidence_assertions):
            assertion = require_mapping(raw_assertion, f"finding {finding_id}.evidence_assertions[{assertion_index}]")
            query_id = require_string(assertion.get("query_id"), f"finding {finding_id}.evidence_assertions[{assertion_index}].query_id")
            query = available_queries.get(query_id) if isinstance(available_queries, dict) else None
            if query_id not in available_query_ids:
                errors.append(f"finding {finding_id} asserts unavailable evidence query: {query_id}")
                continue
            if query is None:
                errors.append(f"finding {finding_id} cannot evaluate evidence assertion without query records: {query_id}")
                continue
            if "match_count" in assertion:
                expected = require_nonnegative_int(assertion.get("match_count"), f"finding {finding_id} evidence assertion {query_id}.match_count", 0)
                actual = query.get("match_count")
                if actual != expected:
                    errors.append(f"finding {finding_id} evidence query {query_id} has match_count {actual!r}; requires {expected}")
            if "capture_count" in assertion:
                expected = require_nonnegative_int(assertion.get("capture_count"), f"finding {finding_id} evidence assertion {query_id}.capture_count", 0)
                actual = len(require_list(query.get("captures"), f"evidence query {query_id}.captures"))
                if actual != expected:
                    errors.append(f"finding {finding_id} evidence query {query_id} has capture_count {actual}; requires {expected}")
            raw_pattern_counts = assertion.get("pattern_capture_counts")
            if raw_pattern_counts is not None:
                expected_pattern_counts = require_mapping(raw_pattern_counts, f"finding {finding_id} evidence assertion {query_id}.pattern_capture_counts")
                actual_pattern_counts: dict[str, int] = {}
                for capture_index, raw_capture in enumerate(require_list(query.get("captures"), f"evidence query {query_id}.captures")):
                    capture = require_mapping(raw_capture, f"evidence query {query_id}.captures[{capture_index}]")
                    pattern_index = capture.get("pattern_index")
                    if isinstance(pattern_index, bool) or not isinstance(pattern_index, int) or pattern_index < 0:
                        raise PacketError(f"evidence query {query_id}.captures[{capture_index}].pattern_index must be a non-negative integer")
                    key = str(pattern_index)
                    actual_pattern_counts[key] = actual_pattern_counts.get(key, 0) + 1
                normalized_expected = {
                    require_string(key, f"finding {finding_id} evidence assertion {query_id}.pattern_capture_counts key"): require_nonnegative_int(value, f"finding {finding_id} evidence assertion {query_id}.pattern_capture_counts[{key}]", 0)
                    for key, value in expected_pattern_counts.items()
                }
                if actual_pattern_counts != normalized_expected:
                    errors.append(f"finding {finding_id} evidence query {query_id} has pattern_capture_counts {actual_pattern_counts}; requires {normalized_expected}")
        raw_inventory_assertion = finding.get("rust_call_inventory")
        if raw_inventory_assertion is not None:
            inventory_assertion = require_mapping(raw_inventory_assertion, f"finding {finding_id}.rust_call_inventory")
            if rust_call_inventory is None:
                errors.append(f"finding {finding_id} requires a Rust call inventory")
            else:
                records = call_inventory_records(rust_call_inventory)
                expected_source = inventory_assertion.get("source")
                if expected_source is not None:
                    expected_source = require_string(expected_source, f"finding {finding_id}.rust_call_inventory.source")
                    actual_source = rust_call_inventory.get("source")
                    if actual_source != expected_source:
                        errors.append(f"finding {finding_id} Rust call inventory source is {actual_source!r}; requires {expected_source!r}")
                expected_call_count = require_nonnegative_int(inventory_assertion.get("call_count"), f"finding {finding_id}.rust_call_inventory.call_count", len(records))
                if len(records) != expected_call_count:
                    errors.append(f"finding {finding_id} Rust call inventory has {len(records)} calls; requires {expected_call_count}")
                owner_count = len({require_string(record.get("owner"), "Rust call inventory record owner") for record in records})
                expected_owner_count = require_nonnegative_int(inventory_assertion.get("owner_count"), f"finding {finding_id}.rust_call_inventory.owner_count", owner_count)
                if owner_count != expected_owner_count:
                    errors.append(f"finding {finding_id} Rust call inventory has {owner_count} owners; requires {expected_owner_count}")
                require_site_keys = inventory_assertion.get("require_site_keys", False)
                if not isinstance(require_site_keys, bool):
                    raise PacketError(f"finding {finding_id}.rust_call_inventory.require_site_keys must be a boolean")
                if require_site_keys:
                    for record in records:
                        site_key = require_string(record.get("site_key"), "Rust call inventory record site_key")
                        if f"`{site_key}`" not in block:
                            errors.append(f"finding {finding_id} does not disposition Rust call site: {site_key}")
        minimum_locators = require_nonnegative_int(finding.get("minimum_source_locators"), f"finding {finding_id}.minimum_source_locators", 1)
        locator_count = len(SOURCE_LOCATOR.findall(block))
        if locator_count < minimum_locators:
            errors.append(f"finding {finding_id} has {locator_count} source locators; requires {minimum_locators}")
        units = verdict_units(block_lines)
        unit_ids = [unit_id for unit_id, _unit_lines in units]
        duplicate_unit_ids = sorted({unit_id for unit_id in unit_ids if unit_ids.count(unit_id) > 1})
        for unit_id in duplicate_unit_ids:
            errors.append(f"finding {finding_id} has duplicate verdict unit: {unit_id}")
        minimum_units = require_nonnegative_int(finding.get("minimum_verdict_units"), f"finding {finding_id}.minimum_verdict_units", 1)
        if len(units) < minimum_units:
            errors.append(f"finding {finding_id} has {len(units)} verdict units; requires {minimum_units}")
        for unit_id, unit_lines in units:
            for label in REQUIRED_UNIT_LABELS:
                present, value = verdict_unit_field(unit_lines, label)
                if not present:
                    errors.append(f"verdict unit {unit_id} is missing label: {label}")
                elif not value:
                    errors.append(f"verdict unit {unit_id} has blank field: {label}")
        finding_forbidden = require_list(finding.get("forbidden_phrases", []), f"finding {finding_id}.forbidden_phrases")
        for phrase_index, raw_phrase in enumerate(finding_forbidden):
            phrase = require_string(raw_phrase, f"finding {finding_id}.forbidden_phrases[{phrase_index}]")
            if phrase.casefold() in block.casefold():
                errors.append(f"finding {finding_id} contains forbidden deferral: {phrase!r}")
    return errors


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--evidence-json", required=True, type=Path)
    parser.add_argument("--rust-call-inventory-json", type=Path)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        packet = arguments.packet.read_text(encoding="utf-8")
        contract = load_json(arguments.contract, "packet contract")
        evidence = load_json(arguments.evidence_json, "source evidence")
        rust_call_inventory = load_json(arguments.rust_call_inventory_json, "Rust call inventory") if arguments.rust_call_inventory_json is not None else None
        errors = validate(packet, contract, evidence_queries_by_id(evidence), rust_call_inventory)
    except (OSError, PacketError) as error:
        print(json.dumps({"status": "invalid-input", "errors": [str(error)]}, indent=2), file=sys.stderr)
        return 2
    result = {"status": "passed" if not errors else "failed", "errors": errors}
    stream = sys.stdout if not errors else sys.stderr
    print(json.dumps(result, indent=2), file=stream)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
