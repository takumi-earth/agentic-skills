#!/usr/bin/env python3
"""Render bounded chronology packets around selected rollout JSONL records."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable

from rollout_records import (
    CALL_KINDS, RESULT_KINDS, bounded_document, event_record, home_text,
    kind, lf_lines, operation_status, record_metadata,
)

def normalize_status(record: dict[str, Any]) -> tuple[str, str, str]:
    status, evidence = operation_status(record)
    confidence = "low" if status in {"unknown", "unsupported"} else "medium" if status == "attempted" else "high"
    return status, evidence, confidence


def payload_value(record: dict[str, Any]) -> Any:
    record = event_record(record)
    for key in ("content", "output", "message", "payload", "arguments"):
        if key in record:
            return record[key]
    return record


def bound_payload(value: Any, limit: int) -> dict[str, Any]:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
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
        "text": home_text(text),
        "original_bytes": len(encoded),
        "emitted_source_bytes": len(emitted),
        "emitted_bytes": len(home_text(text).encode("utf-8")),
        "omitted_bytes": len(encoded) - len(emitted),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "truncated": len(emitted) < len(encoded),
    }


def record_ordinal(record: Any) -> int | None:
    return record_metadata(record)["ordinal"] if isinstance(record, dict) else None


def packet_for(line_number: int, raw: bytes, payload_limit: int) -> dict[str, Any]:
    try:
        record = json.loads(raw)
    except (ValueError, RecursionError) as error:
        return {
            "source_line": line_number,
            "raw_record_sha256": hashlib.sha256(raw).hexdigest(),
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
            "raw_record_sha256": hashlib.sha256(raw).hexdigest(),
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
    meta = record_metadata(record)
    return {
        "source_line": line_number,
        "raw_record_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_ordinal": record_ordinal(record),
        "record_kind": meta["kind"],
        "role": meta["role"],
        "tool": meta["tool"],
        "call_id": meta["call_id"],
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
        except (ValueError, RecursionError):
            continue
        ordinal = record_ordinal(record)
        if ordinal is not None:
            ordinal_map.setdefault(ordinal, []).append(line_number)
    for ordinal in ordinal_anchors:
        matches = ordinal_map.get(ordinal, [])
        if not matches:
            errors.append(f"ordinal anchor was not found: {ordinal}")
        elif len(matches) > 1:
            errors.append(f"ordinal anchor {ordinal} matches multiple source lines: {matches}")
        anchors.update(matches)
    selected: set[int] = set()
    for anchor in anchors:
        selected.update(range(max(1, anchor - before), min(len(raw_lines), anchor + after) + 1))
    return sorted(selected), errors


def correlate(packets: list[dict[str, Any]], raw_lines: list[bytes], selected: list[int]) -> int:
    """Pair unique supported call/result records, including partners outside the window."""
    index: dict[str, dict[str, list[int]]] = {}
    unsupported = 0
    for line_number, raw in enumerate(raw_lines, start=1):
        try:
            record = json.loads(raw)
            if not isinstance(record, dict):
                unsupported += 1
                continue
            meta = record_metadata(record)
        except (ValueError, RecursionError):
            unsupported += 1
            continue
        if meta["call_id"] is not None and kind(record) in CALL_KINDS | RESULT_KINDS:
            phase = "calls" if kind(record) in CALL_KINDS else "results"
            index.setdefault(meta["call_id"], {"calls": [], "results": []})[phase].append(line_number)
    for packet in packets:
        packet["correlation"] = correlation_for(packet, index, set(selected))
    return unsupported


def correlation_for(packet: dict[str, Any], index: dict[str, dict[str, list[int]]], selected: set[int]) -> dict[str, Any]:
    event_kind = packet["record_kind"]
    call_id = packet["call_id"]
    if event_kind not in CALL_KINDS | RESULT_KINDS:
        return {"state": "known-id" if call_id else "not-applicable", "partner_lines": []}
    if call_id is None:
        return {"state": "missing-call-id", "partner_lines": []}
    pair = index[call_id]
    partners = pair["results" if event_kind in CALL_KINDS else "calls"]
    if len(pair["calls"]) > 1 or len(pair["results"]) > 1:
        state = "ambiguous"
    elif not partners:
        state = "unmatched"
    else:
        state = "matched" if partners[0] in selected else "partner-outside-window"
    return {"state": state, "partner_lines": partners}


def render(path: Path, args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    try:
        source = path.expanduser().read_bytes()
    except (OSError, ValueError, RuntimeError) as error:
        return 2, {"status": "error", "errors": [str(error)]}
    raw_lines = lf_lines(source)
    lines, errors = selected_lines(raw_lines, args.line, args.ordinal, args.before, args.after)
    if not lines:
        if not errors:
            errors.append("at least one --line or --ordinal anchor is required")
        return 1, {"status": "invalid-selection", "errors": errors, "packets": []}
    packets = [packet_for(line, raw_lines[line - 1], args.payload_bytes) for line in lines]
    unsupported = correlate(packets, raw_lines, lines)
    return (1 if errors else 0), {
        "schema_version": 1,
        "status": "partial" if errors else "ok",
        "source": path.as_posix(),
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "selection_errors": errors,
        "correlation_unsupported_lines": unsupported,
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
    parser.add_argument("--max-bytes", type=int, default=20000)
    args = parser.parse_args(argv)
    if args.before < 0 or args.after < 0 or args.payload_bytes < 1 or args.max_bytes < 128:
        code, result = 2, {"status": "invalid-selection", "errors": ["windows must be nonnegative, payload bytes positive, and max-bytes >= 128"]}
    else:
        try:
            code, result = render(args.rollout, args)
        except (ValueError, TypeError, RecursionError, OverflowError):
            code, result = 2, {"status": "invalid-input", "errors": ["unsupported record value or nesting"]}
    try:
        encoded = bounded_document(result, max(128, args.max_bytes), "packets")
    except (ValueError, TypeError, RecursionError, OverflowError):
        code = 2
        encoded = bounded_document({"status": "invalid-input", "errors": ["unsupported presentation value or nesting"]}, max(128, args.max_bytes), "packets")
    sys.stdout.buffer.write(encoded)
    return code


if __name__ == "__main__":
    sys.exit(main())
