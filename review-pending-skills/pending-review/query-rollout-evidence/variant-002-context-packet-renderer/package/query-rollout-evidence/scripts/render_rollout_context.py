#!/usr/bin/env python3
"""Render bounded chronology packets around selected rollout JSONL records."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable


def find_key(value: Any, keys: tuple[str, ...]) -> Any:
    if isinstance(value, dict):
        for key in keys:
            if key in value:
                return value[key]
        for child in value.values():
            found = find_key(child, keys)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_key(child, keys)
            if found is not None:
                return found
    return None


def normalize_status(record: dict[str, Any]) -> tuple[str, str, str]:
    explicit = find_key(record, ("status", "state"))
    exit_code = find_key(record, ("exit_code", "exit_status"))
    kind = str(find_key(record, ("kind", "type")) or "").lower()
    explicit_text = str(explicit).lower() if explicit is not None else ""
    success = explicit_text in {"success", "passed", "completed", "complete", "ok"}
    failure = explicit_text in {"failed", "failure", "error"}
    if isinstance(exit_code, int) and not isinstance(exit_code, bool):
        if (exit_code == 0 and failure) or (exit_code != 0 and success):
            return "ambiguous", "explicit-status and exit-code conflict", "high"
        return ("completed" if exit_code == 0 else "failed"), "exit-code", "high"
    if success or failure:
        return ("completed" if success else "failed"), "explicit-status", "medium"
    if "tool_call" in kind or kind.endswith("call"):
        return "attempted", "record-kind", "medium"
    if "tool_result" in kind or "output" in kind:
        return "completed", "record-kind", "low"
    return "unknown", "no status evidence", "low"


def payload_value(record: dict[str, Any]) -> Any:
    for key in ("content", "output", "message", "payload", "arguments"):
        if key in record:
            return record[key]
    return record


def bound_payload(value: Any, limit: int) -> dict[str, Any]:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    emitted = encoded[:limit]
    while emitted:
        try:
            text = emitted.decode("utf-8")
            break
        except UnicodeDecodeError:
            emitted = emitted[:-1]
    else:
        text = ""
    return {
        "text": text,
        "original_bytes": len(encoded),
        "emitted_bytes": len(emitted),
        "omitted_bytes": len(encoded) - len(emitted),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "truncated": len(emitted) < len(encoded),
    }


def record_ordinal(record: Any) -> int | None:
    value = find_key(record, ("raw_ordinal", "ordinal"))
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def packet_for(line_number: int, raw: bytes, payload_limit: int) -> dict[str, Any]:
    try:
        record = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        return {
            "source_line": line_number,
            "raw_ordinal": None,
            "record_kind": "malformed",
            "role": None,
            "tool": None,
            "call_id": None,
            "status": "unsupported",
            "status_evidence": str(error),
            "status_confidence": "high",
            "payload": bound_payload(raw.decode("utf-8", errors="replace"), payload_limit),
        }
    if not isinstance(record, dict):
        return {
            "source_line": line_number,
            "raw_ordinal": record_ordinal(record),
            "record_kind": f"unsupported-{type(record).__name__}",
            "role": None,
            "tool": None,
            "call_id": None,
            "status": "unsupported",
            "status_evidence": "top-level record is not an object",
            "status_confidence": "high",
            "payload": bound_payload(record, payload_limit),
        }
    status, evidence, confidence = normalize_status(record)
    kind = find_key(record, ("kind", "type", "event_type"))
    role = find_key(record, ("role",))
    tool = find_key(record, ("tool_name", "tool"))
    call_id = find_key(record, ("call_id",))
    return {
        "source_line": line_number,
        "raw_ordinal": record_ordinal(record),
        "record_kind": str(kind) if kind is not None else "object",
        "role": str(role) if role is not None else None,
        "tool": str(tool) if tool is not None else None,
        "call_id": str(call_id) if call_id is not None else None,
        "status": status,
        "status_evidence": evidence,
        "status_confidence": confidence,
        "payload": bound_payload(payload_value(record), payload_limit),
    }


def selected_lines(
    raw_lines: list[bytes],
    line_anchors: Iterable[int],
    ordinal_anchors: Iterable[int],
    before: int,
    after: int,
) -> tuple[list[int], list[str]]:
    anchors: set[int] = set()
    errors: list[str] = []
    for line in line_anchors:
        if line < 1 or line > len(raw_lines):
            errors.append(f"line anchor is out of range: {line}")
        else:
            anchors.add(line)
    ordinal_map: dict[int, list[int]] = {}
    for line_number, raw in enumerate(raw_lines, start=1):
        try:
            record = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        ordinal = record_ordinal(record)
        if ordinal is not None:
            ordinal_map.setdefault(ordinal, []).append(line_number)
    for ordinal in ordinal_anchors:
        matches = ordinal_map.get(ordinal, [])
        if not matches:
            errors.append(f"ordinal anchor was not found: {ordinal}")
        anchors.update(matches)
    selected: set[int] = set()
    for anchor in anchors:
        selected.update(range(max(1, anchor - before), min(len(raw_lines), anchor + after) + 1))
    return sorted(selected), errors


def render(path: Path, args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    try:
        source = path.read_bytes()
    except OSError as error:
        return 2, {"status": "error", "errors": [str(error)]}
    raw_lines = source.splitlines()
    lines, errors = selected_lines(raw_lines, args.line, args.ordinal, args.before, args.after)
    if not lines:
        if not errors:
            errors.append("at least one --line or --ordinal anchor is required")
        return 1, {"status": "invalid-selection", "errors": errors, "packets": []}
    packets = [packet_for(line, raw_lines[line - 1], args.payload_bytes) for line in lines]
    return (1 if errors else 0), {
        "schema_version": 1,
        "status": "partial" if errors else "ok",
        "source": path.as_posix(),
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "selection_errors": errors,
        "packets": packets,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rollout", type=Path)
    parser.add_argument("--line", type=int, action="append", default=[])
    parser.add_argument("--ordinal", type=int, action="append", default=[])
    parser.add_argument("--before", type=int, default=2)
    parser.add_argument("--after", type=int, default=2)
    parser.add_argument("--payload-bytes", type=int, default=4000)
    args = parser.parse_args(argv)
    if args.before < 0 or args.after < 0 or args.payload_bytes < 1:
        parser.error("window bounds must be nonnegative and payload bytes positive")
    code, result = render(args.rollout, args)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
