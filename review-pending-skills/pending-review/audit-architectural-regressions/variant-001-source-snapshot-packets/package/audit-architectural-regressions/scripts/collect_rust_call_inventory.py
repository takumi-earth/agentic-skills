#!/usr/bin/env python3
"""Collect enclosing owners and identity arguments for reviewed Rust call sites."""

from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
import json
from pathlib import Path
import re
import sys
from typing import Any

from collect_source_evidence import atomic_write
from collect_source_evidence import normalize_home


SCHEMA_VERSION = 1


class InventoryError(Exception):
    """Raised when a Rust call-inventory specification or source is invalid."""


def require_mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InventoryError(f"{label} must be an object")
    return value


def require_list(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise InventoryError(f"{label} must be an array")
    return value


def require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise InventoryError(f"{label} must be a non-empty string")
    return value


def mask_rust_noncode(source: str) -> str:
    """Replace comments and literals with spaces while preserving offsets and newlines."""
    masked = list(source)
    index = 0
    length = len(source)

    def erase(start: int, end: int) -> None:
        for position in range(start, end):
            if masked[position] != "\n":
                masked[position] = " "

    while index < length:
        if source.startswith("//", index):
            end = source.find("\n", index + 2)
            end = length if end == -1 else end
            erase(index, end)
            index = end
            continue
        if source.startswith("/*", index):
            depth = 1
            cursor = index + 2
            while cursor < length and depth:
                if source.startswith("/*", cursor):
                    depth += 1
                    cursor += 2
                elif source.startswith("*/", cursor):
                    depth -= 1
                    cursor += 2
                else:
                    cursor += 1
            if depth:
                raise InventoryError("unterminated Rust block comment")
            erase(index, cursor)
            index = cursor
            continue
        raw_match = re.match(r"(?:br|rb|r)(?P<hashes>#{0,255})\"", source[index:])
        if raw_match is not None:
            hashes = raw_match.group("hashes")
            terminator = '"' + hashes
            content_start = index + raw_match.end()
            end = source.find(terminator, content_start)
            if end == -1:
                raise InventoryError("unterminated Rust raw string")
            end += len(terminator)
            erase(index, end)
            index = end
            continue
        prefix_length = 2 if source.startswith('b"', index) else 1 if source[index] == '"' else 0
        if prefix_length:
            cursor = index + prefix_length
            escaped = False
            while cursor < length:
                character = source[cursor]
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    cursor += 1
                    break
                cursor += 1
            else:
                raise InventoryError("unterminated Rust string")
            erase(index, cursor)
            index = cursor
            continue
        if source[index] == "'":
            cursor = index + 1
            escaped = False
            found_end = False
            while cursor < min(length, index + 12):
                character = source[cursor]
                if character == "\n":
                    break
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == "'":
                    cursor += 1
                    found_end = True
                    break
                cursor += 1
            if found_end:
                erase(index, cursor)
                index = cursor
                continue
        index += 1
    return "".join(masked)


def matching_parenthesis(masked: str, open_index: int) -> int:
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack = [")"]
    index = open_index + 1
    while index < len(masked):
        character = masked[index]
        if character in pairs:
            stack.append(pairs[character])
        elif stack and character == stack[-1]:
            stack.pop()
            if not stack:
                return index
        index += 1
    raise InventoryError(f"call at offset {open_index} has no closing parenthesis")


def split_arguments(source: str, masked: str, start: int, end: int) -> list[str]:
    arguments: list[str] = []
    stack: list[str] = []
    pairs = {"(": ")", "[": "]", "{": "}"}
    argument_start = start
    for index in range(start, end):
        character = masked[index]
        if character in pairs:
            stack.append(pairs[character])
        elif stack and character == stack[-1]:
            stack.pop()
        elif character == "," and not stack:
            arguments.append(source[argument_start:index].strip())
            argument_start = index + 1
    trailing = source[argument_start:end].strip()
    if trailing:
        arguments.append(trailing)
    return arguments


def normalize_argument(argument: str) -> str:
    return " ".join(argument.split())


def display_identity_value(value: str) -> str:
    """Render a Rust identity expression compactly without losing dynamic selectors."""
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return value
    return decoded if isinstance(decoded, str) else value


def site_key(owner: str, identity: dict[str, str]) -> str:
    """Build the stable owner-plus-selector key used by verdict packet coverage."""
    rendered = ";".join(f"{label}={display_identity_value(value)}" for label, value in identity.items())
    return f"{owner}::{rendered}"


def compile_pattern(raw_pattern: object, label: str) -> re.Pattern[str]:
    pattern = require_string(raw_pattern, label)
    try:
        return re.compile(pattern, re.MULTILINE)
    except re.error as error:
        raise InventoryError(f"{label} has invalid pattern {pattern!r}: {error}") from error


def collect(spec_path: Path) -> dict[str, Any]:
    try:
        spec = require_mapping(json.loads(spec_path.read_text(encoding="utf-8")), "specification")
    except (OSError, json.JSONDecodeError) as error:
        raise InventoryError(f"failed to read inventory specification: {error}") from error
    if spec.get("schema_version") != SCHEMA_VERSION:
        raise InventoryError(f"specification schema_version must be {SCHEMA_VERSION}")
    source_path_value = Path(require_string(spec.get("source"), "source")).expanduser()
    source_path = source_path_value if source_path_value.is_absolute() else spec_path.parent / source_path_value
    source_path = source_path.resolve()
    try:
        source = source_path.read_text(encoding="utf-8")
    except OSError as error:
        raise InventoryError(f"failed to read Rust source {source_path}: {error}") from error
    scope_end = spec.get("scope_end_pattern")
    if scope_end is not None:
        scope_pattern = compile_pattern(scope_end, "scope_end_pattern")
        scope_match = scope_pattern.search(source)
        if scope_match is None:
            raise InventoryError("scope_end_pattern matched no source")
        source = source[: scope_match.start()]
    masked = mask_rust_noncode(source)
    owner_pattern = compile_pattern(spec.get("owner_pattern"), "owner_pattern")
    owner_matches = list(owner_pattern.finditer(source))
    owner_offsets = [match.start() for match in owner_matches]
    call_specs = require_list(spec.get("calls"), "calls")
    if not call_specs:
        raise InventoryError("calls must not be empty")
    configured: dict[str, tuple[list[int], list[str]]] = {}
    for index, raw_call in enumerate(call_specs):
        call = require_mapping(raw_call, f"calls[{index}]")
        callee = require_string(call.get("callee"), f"calls[{index}].callee")
        raw_indices = require_list(call.get("identity_args"), f"calls[{index}].identity_args")
        raw_labels = require_list(call.get("identity_labels"), f"calls[{index}].identity_labels")
        if len(raw_indices) != len(raw_labels) or not raw_indices:
            raise InventoryError(f"calls[{index}] identity_args and identity_labels must have the same non-zero length")
        indices: list[int] = []
        labels: list[str] = []
        for identity_index, raw_identity_index in enumerate(raw_indices):
            if isinstance(raw_identity_index, bool) or not isinstance(raw_identity_index, int) or raw_identity_index < 0:
                raise InventoryError(f"calls[{index}].identity_args[{identity_index}] must be a non-negative integer")
            indices.append(raw_identity_index)
            labels.append(require_string(raw_labels[identity_index], f"calls[{index}].identity_labels[{identity_index}]"))
        if callee in configured:
            raise InventoryError(f"duplicate call specification: {callee}")
        configured[callee] = (indices, labels)
    line_starts = [0]
    line_starts.extend(match.end() for match in re.finditer("\n", source))
    records: list[dict[str, Any]] = []
    for callee, (indices, labels) in configured.items():
        pattern = re.compile(rf"\b{re.escape(callee)}\s*\(")
        for match in pattern.finditer(masked):
            line_start = source.rfind("\n", 0, match.start()) + 1
            if re.search(r"\bfn\s*$", source[line_start : match.start()]):
                continue
            open_index = masked.find("(", match.start(), match.end())
            close_index = matching_parenthesis(masked, open_index)
            arguments = split_arguments(source, masked, open_index + 1, close_index)
            maximum_index = max(indices)
            if maximum_index >= len(arguments):
                line_number = bisect_right(line_starts, match.start())
                raise InventoryError(f"{callee} at line {line_number} has {len(arguments)} arguments; identity index {maximum_index} is unavailable")
            owner_position = bisect_right(owner_offsets, match.start()) - 1
            if owner_position < 0:
                line_number = bisect_right(line_starts, match.start())
                raise InventoryError(f"{callee} at line {line_number} has no enclosing owner match")
            owner_match = owner_matches[owner_position]
            owner_groups = owner_match.groupdict()
            owner = owner_groups.get("owner")
            if owner is None:
                raise InventoryError("owner_pattern must define a named `owner` capture")
            identity = {
                label: normalize_argument(arguments[argument_index])
                for argument_index, label in zip(indices, labels, strict=True)
            }
            record_site_key = site_key(owner, identity)
            records.append(
                {
                    "owner": owner,
                    "owner_line": bisect_right(line_starts, owner_match.start()),
                    "callee": callee,
                    "line": bisect_right(line_starts, match.start()),
                    "identity": identity,
                    "site_key": record_site_key,
                }
            )
    records.sort(key=lambda record: (record["line"], record["callee"]))
    site_key_counts = Counter(record["site_key"] for record in records)
    duplicate_site_keys = sorted(site_key for site_key, count in site_key_counts.items() if count > 1)
    if duplicate_site_keys:
        raise InventoryError("duplicate call-site keys: " + ", ".join(duplicate_site_keys))
    return {
        "schema_version": SCHEMA_VERSION,
        "source": normalize_home(str(source_path)),
        "call_count": len(records),
        "owner_count": len({record["owner"] for record in records}),
        "calls": records,
    }


def render_markdown(inventory: dict[str, Any]) -> str:
    output = [
        "# Rust structural call inventory",
        "",
        f"Source: `{inventory['source']}`",
        "",
        f"Calls: `{inventory['call_count']}`",
        "",
        f"Owners: `{inventory['owner_count']}`",
        "",
        "| Owner | Owner line | Call | Call line | Identity | Stable site key |",
        "|---|---:|---|---:|---|---|",
    ]
    for record in inventory["calls"]:
        identity = "; ".join(f"{label}={value}" for label, value in record["identity"].items())
        output.append(f"| `{record['owner']}` | `{record['owner_line']}` | `{record['callee']}` | `{record['line']}` | `{identity}` | `{record['site_key']}` |")
    return "\n".join(output) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    try:
        inventory = collect(arguments.spec)
        atomic_write(arguments.output_json, json.dumps(inventory, indent=2) + "\n")
        atomic_write(arguments.output_markdown, render_markdown(inventory))
    except InventoryError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
