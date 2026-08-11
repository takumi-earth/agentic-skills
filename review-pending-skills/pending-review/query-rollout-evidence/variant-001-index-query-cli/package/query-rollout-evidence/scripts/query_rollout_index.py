#!/usr/bin/env python3
"""Query normalized rollout JSONL with typed filters and bounded output."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def nested_values(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        for item in value.values():
            yield from nested_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from nested_values(item)
    else:
        yield value


def find_key(value: Any, keys: tuple[str, ...]) -> Any:
    if isinstance(value, dict):
        for key in keys:
            if key in value:
                return value[key]
        for child in value.values():
            result = find_key(child, keys)
            if result is not None:
                return result
    elif isinstance(value, list):
        for child in value:
            result = find_key(child, keys)
            if result is not None:
                return result
    return None


def normalize_status(record: dict[str, Any]) -> tuple[str, str]:
    explicit = find_key(record, ("status", "state"))
    exit_code = find_key(record, ("exit_code", "exit_status"))
    kind = str(find_key(record, ("kind", "type")) or "").lower()
    explicit_text = str(explicit).lower() if explicit is not None else ""
    explicit_success = explicit_text in {"success", "passed", "completed", "complete", "ok"}
    explicit_failure = explicit_text in {"failed", "failure", "error"}
    if isinstance(exit_code, int) and not isinstance(exit_code, bool):
        if (exit_code == 0 and explicit_failure) or (exit_code != 0 and explicit_success):
            return "ambiguous", "explicit-status-conflicts-with-exit-code"
        return ("completed" if exit_code == 0 else "failed"), "exit-code"
    if explicit_success:
        return "completed", "explicit-status"
    if explicit_failure:
        return "failed", "explicit-status"
    if "tool_call" in kind or kind.endswith("call"):
        return "attempted", "record-kind"
    if "tool_result" in kind or "output" in kind:
        return "completed", "record-kind"
    return "unsupported", "no-status-evidence"


def metadata(record: dict[str, Any], source_line: int) -> dict[str, Any]:
    ordinal = find_key(record, ("raw_ordinal", "ordinal"))
    kind = find_key(record, ("kind", "type", "event_type"))
    tool = find_key(record, ("tool_name", "tool", "name"))
    call_id = find_key(record, ("call_id",))
    classification = find_key(record, ("candidate_class", "classification"))
    status, status_evidence = normalize_status(record)
    return {
        "source_line": source_line,
        "ordinal": ordinal if isinstance(ordinal, int) and not isinstance(ordinal, bool) else None,
        "kind": str(kind) if kind is not None else None,
        "tool": str(tool) if tool is not None else None,
        "call_id": str(call_id) if call_id is not None else None,
        "classification": str(classification) if classification is not None else None,
        "status": status,
        "status_evidence": status_evidence,
    }


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
    scalar_text = "\n".join(str(value) for value in nested_values(record) if isinstance(value, (str, int, float, bool)))
    if args.path_contains is not None and args.path_contains not in scalar_text:
        return False
    if output_pattern is not None and output_pattern.search(scalar_text) is None:
        return False
    return True


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
        "emitted_preview": preview,
        "emitted_bytes": len(preview_bytes),
        "omitted_bytes": len(payload) - len(preview_bytes),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }, len(payload) - len(preview_bytes)


def query(path: Path, args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    try:
        source_bytes = path.read_bytes()
    except OSError as error:
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
    emitted_row_bytes = 0
    for line_number, raw_line in enumerate(source_bytes.splitlines(), start=1):
        try:
            record = json.loads(raw_line)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            malformed.append({"source_line": line_number, "error": str(error)})
            continue
        if not isinstance(record, dict):
            unsupported.append({"source_line": line_number, "shape": type(record).__name__})
            continue
        meta = metadata(record, line_number)
        if not matches(record, meta, args, output_pattern):
            continue
        rendered, row_omitted = bounded_record(record, args.record_bytes)
        row = {**meta, "record_hash": hashlib.sha256(canonical(record)).hexdigest(), "record": rendered}
        row_bytes = len(canonical(row))
        if len(matched_rows) >= args.max_rows or emitted_row_bytes + row_bytes > args.max_bytes:
            omitted_rows += 1
            omitted_bytes += len(canonical(record))
            continue
        matched_rows.append(row)
        emitted_row_bytes += row_bytes
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
    parser.add_argument("--status", choices=["attempted", "completed", "failed", "ambiguous", "unsupported"])
    parser.add_argument("--classification")
    parser.add_argument("--output-pattern")
    parser.add_argument("--max-rows", type=int, default=50)
    parser.add_argument("--max-bytes", type=int, default=20000)
    parser.add_argument("--record-bytes", type=int, default=4000)
    args = parser.parse_args(argv)
    if args.max_rows < 0 or args.max_bytes < 1 or args.record_bytes < 1:
        parser.error("bounds must be nonnegative rows and positive bytes")
    code, result = query(args.index, args)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
