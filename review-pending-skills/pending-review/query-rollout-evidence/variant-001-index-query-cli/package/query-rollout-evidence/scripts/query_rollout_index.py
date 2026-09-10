#!/usr/bin/env python3
"""Query normalized rollout JSONL with typed filters and bounded output."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from rollout_records import (
    RESULT_KINDS, bounded_document, event_record, home_text, kind, lf_lines,
    object_value, operation_status, record_metadata, serialized,
)


def canonical(value: Any) -> bytes:
    return serialized(value)[:-1]


def normalize_status(record: dict[str, Any]) -> tuple[str, str]:
    return operation_status(record)


def metadata(record: dict[str, Any], source_line: int) -> dict[str, Any]:
    status, status_evidence = normalize_status(record)
    return {
        **record_metadata(record),
        "source_line": source_line,
        "status": status,
        "status_evidence": status_evidence,
    }


def _event_paths(event: dict[str, Any]) -> list[str]:
    paths = []
    for owner in (event, object_value(event.get("arguments"))):
        for key in ("path", "file_path", "target_path", "source_path", "paths", "files"):
            value = owner.get(key)
            values = value if isinstance(value, list) else [value]
            paths.extend(path for path in values if isinstance(path, str))
    return paths


def _output_matches(record: dict[str, Any], pattern: re.Pattern[str]) -> bool:
    if kind(record) not in RESULT_KINDS:
        return False
    event = event_record(record)
    for key in ("output", "stdout", "stderr", "result", "tool_response"):
        if key in event:
            output = event[key]
            text = output if isinstance(output, str) else canonical(output).decode("utf-8")
            if pattern.search(text):
                return True
    return False


def matches(record: dict[str, Any], meta: dict[str, Any], args: argparse.Namespace, output_pattern: re.Pattern[str] | None) -> bool:
    ordinal = meta["ordinal"]
    if args.ordinal_min is not None and (ordinal is None or ordinal < args.ordinal_min):
        return False
    if args.ordinal_max is not None and (ordinal is None or ordinal > args.ordinal_max):
        return False
    for attribute in ("kind", "tool", "call_id", "status", "classification"):
        expected = getattr(args, attribute)
        if expected is not None and meta[attribute] != expected:
            return False
    if args.path_contains is not None:
        if not any(args.path_contains in path for path in _event_paths(event_record(record))):
            return False
    return output_pattern is None or _output_matches(record, output_pattern)


def bounded_record(record: dict[str, Any], limit: int) -> tuple[Any, int]:
    payload = canonical(record)
    if len(payload) <= limit:
        return record, 0
    preview_bytes = payload[:limit]
    while preview_bytes:
        try:
            preview = preview_bytes.decode("utf-8")
            break
        except UnicodeDecodeError:
            preview_bytes = preview_bytes[:-1]
    else:
        preview = ""
    return {
        "truncated": True,
        "original_bytes": len(payload),
        "emitted_preview": home_text(preview),
        "emitted_source_bytes": len(preview_bytes),
        "emitted_bytes": len(home_text(preview).encode("utf-8")),
        "omitted_bytes": len(payload) - len(preview_bytes),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }, len(payload) - len(preview_bytes)


def query(path: Path, args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    try:
        source_bytes = path.expanduser().read_bytes()
    except (OSError, ValueError, RuntimeError) as error:
        return 2, {"status": "error", "errors": [str(error)]}
    try:
        output_pattern = re.compile(args.output_pattern) if args.output_pattern is not None else None
    except re.error as error:
        return 2, {"status": "invalid-filter", "errors": [str(error)]}
    matched_rows: list[dict[str, Any]] = []
    malformed: list[dict[str, Any]] = []
    unsupported: list[dict[str, Any]] = []
    omitted_rows = 0
    omitted_bytes = 0
    for line_number, raw_line in enumerate(lf_lines(source_bytes), start=1):
        try:
            record = json.loads(raw_line)
        except (ValueError, RecursionError) as error:
            malformed.append({"source_line": line_number, "error": str(error)})
            continue
        if not isinstance(record, dict):
            unsupported.append({"source_line": line_number, "shape": type(record).__name__})
            continue
        try:
            meta = metadata(record, line_number)
            if not matches(record, meta, args, output_pattern):
                continue
            rendered, row_omitted = bounded_record(record, args.record_bytes)
            row = {**meta, "record_hash": hashlib.sha256(canonical(record)).hexdigest(), "raw_record_sha256": hashlib.sha256(raw_line).hexdigest(), "record": rendered}
        except (ValueError, TypeError, RecursionError, OverflowError):
            unsupported.append({"source_line": line_number, "shape": "unsupported-record", "error": "unsupported metadata, value, or nesting"})
            continue
        if len(matched_rows) >= args.max_rows:
            omitted_rows += 1
            omitted_bytes += len(canonical(record))
            continue
        matched_rows.append(row)
        omitted_bytes += row_omitted
    result = {
        "schema_version": 1,
        "status": "ok",
        "source": path.as_posix(),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "filters": {
            "ordinal_min": args.ordinal_min,
            "ordinal_max": args.ordinal_max,
            "kind": args.kind,
            "tool": args.tool,
            "call_id": args.call_id,
            "path_contains": args.path_contains,
            "status": args.status,
            "classification": args.classification,
            "output_pattern": args.output_pattern,
        },
        "matched_rows": matched_rows,
        "emitted_row_count": len(matched_rows),
        "omitted_row_count": omitted_rows,
        "omitted_bytes": omitted_bytes,
        "malformed": malformed,
        "unsupported": unsupported,
    }
    return 0, result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", type=Path)
    parser.add_argument("--ordinal-min", type=int)
    parser.add_argument("--ordinal-max", type=int)
    parser.add_argument("--kind")
    parser.add_argument("--tool")
    parser.add_argument("--call-id")
    parser.add_argument("--path-contains")
    parser.add_argument("--status", choices=["attempted", "completed", "failed", "ambiguous", "unknown", "unsupported"])
    parser.add_argument("--classification")
    parser.add_argument("--output-pattern")
    parser.add_argument("--max-rows", type=int, default=50)
    parser.add_argument("--max-bytes", type=int, default=20000)
    parser.add_argument("--record-bytes", type=int, default=4000)
    args = parser.parse_args(argv)
    if args.max_rows < 0 or args.max_bytes < 128 or args.record_bytes < 1:
        code, result = 2, {"status": "invalid-filter", "errors": ["bounds require nonnegative rows, positive record bytes, and max-bytes >= 128"]}
    elif args.ordinal_min is not None and args.ordinal_max is not None and args.ordinal_min > args.ordinal_max:
        code, result = 2, {"status": "invalid-filter", "errors": ["ordinal-min must not exceed ordinal-max"]}
    else:
        code, result = query(args.index, args)
    try:
        encoded = bounded_document(result, max(128, args.max_bytes), "matched_rows")
    except (ValueError, TypeError, RecursionError, OverflowError):
        code = 2
        encoded = bounded_document({"status": "invalid-input", "errors": ["unsupported value or nesting in selected records"]}, max(128, args.max_bytes), "matched_rows")
    sys.stdout.buffer.write(encoded)
    return code


if __name__ == "__main__":
    sys.exit(main())
