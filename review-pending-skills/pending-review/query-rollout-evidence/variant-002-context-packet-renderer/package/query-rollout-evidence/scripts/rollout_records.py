"""Supported rollout record layouts and bounded presentation; never infer authority."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


CALL_KINDS = {"tool_call", "function_call", "custom_tool_call", "tool_use"}
RESULT_KINDS = {"tool_result", "tool_output", "function_call_output", "custom_tool_call_output"}


def first(record: dict[str, Any], keys: tuple[str, ...]) -> Any:
    return next((record[key] for key in keys if key in record), None)


def event_record(record: dict[str, Any]) -> dict[str, Any]:
    """Unwrap only declared Codex envelopes; message contents remain payload."""
    if first(record, ("kind", "type")) in ("response_item", "event_msg"):
        payload = record.get("payload")
        return payload if isinstance(payload, dict) else {}
    return record


def kind(record: dict[str, Any]) -> str:
    event = event_record(record)
    value = first(event, ("kind", "type", "event_type"))
    return value if isinstance(value, str) else "object"


def object_value(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, RecursionError):
            return {}
    return value if isinstance(value, dict) else {}


def record_metadata(record: dict[str, Any]) -> dict[str, Any]:
    event = event_record(record)
    event_kind = kind(record)
    ordinal = first(record, ("raw_ordinal", "ordinal"))
    call_id = first(event, ("call_id", "tool_use_id"))
    if call_id is None and event_kind in CALL_KINDS:
        call_id = event.get("id")
    metadata = {
        "ordinal": ordinal if isinstance(ordinal, int) and not isinstance(ordinal, bool) else None,
        "kind": event_kind,
        "role": event.get("role"),
        "tool": first(event, ("tool_name", "tool", "name")) if event_kind in CALL_KINDS | RESULT_KINDS else None,
        "call_id": call_id if isinstance(call_id, str) and call_id else None,
        "classification": first(record, ("candidate_class", "classification")),
    }
    for field in ("role", "tool", "classification"):
        if not isinstance(metadata[field], str):
            metadata[field] = None
    return metadata


def operation_status(record: dict[str, Any]) -> tuple[str, str]:
    event = event_record(record)
    event_kind = kind(record)
    result = object_value(first(event, ("output", "result", "tool_response"))) if event_kind in RESULT_KINDS else {}
    explicit = first(event, ("status", "state"))
    nested = first(result, ("status", "state"))
    states = {value.lower() for value in (explicit, nested) if isinstance(value, str)}
    if "ambiguous" in states:
        return "ambiguous", "explicit-uncertainty"
    if "unknown" in states:
        return "unknown", "explicit-uncertainty"
    if "unsupported" in states:
        return "unsupported", "explicit-uncertainty"
    success = bool(states & {"success", "passed", "ok"})
    failure = bool(states & {"failed", "failure", "error"})
    codes = [first(owner, ("exit_code", "exit_status")) for owner in (event, result)]
    known_codes = {code for code in codes if isinstance(code, int) and not isinstance(code, bool)}
    if len(known_codes) > 1:
        return "ambiguous", "conflicting-exit-codes"
    exit_code = next(iter(known_codes), None)
    if isinstance(exit_code, int) and not isinstance(exit_code, bool):
        if (exit_code == 0 and failure) or (exit_code != 0 and success):
            return "ambiguous", "explicit-status-conflicts-with-exit-code"
        return ("completed" if exit_code == 0 else "failed"), "exit-code"
    if success and failure:
        return "ambiguous", "conflicting-operation-statuses"
    if success or failure:
        return ("completed" if success else "failed"), "explicit-status"
    if states & {"complete", "completed"} or event_kind in RESULT_KINDS:
        return "unknown", "transport-completed-operation-unknown"
    if event_kind in CALL_KINDS:
        return "attempted", "record-kind"
    return "unsupported", "no-status-evidence"


def lf_lines(source: bytes) -> list[bytes]:
    lines = source.split(b"\n")
    return lines[:-1] if lines[-1] == b"" else lines


def home_text(value: str) -> str:
    home = re.escape(str(Path.home().resolve(strict=False)))
    value = re.sub(rf"""(["'`]){home}\1""", r"\1~\1", value)
    return re.sub(r"""(?<![^\s"'`=:(\[{])""" + home + r"(?=/|$)", "~", value)


def presentation(value: Any, depth: int = 0) -> Any:
    """Normalize display only; callers hash original input before this step."""
    if depth > 64:
        raise ValueError("record nesting exceeds supported presentation depth")
    if isinstance(value, str):
        return home_text(value)
    if isinstance(value, list):
        return [presentation(item, depth + 1) for item in value]
    if isinstance(value, dict):
        normalized = {home_text(key): presentation(item, depth + 1) for key, item in value.items()}
        if len(normalized) != len(value):
            raise ValueError("path normalization would collapse record keys")
        return normalized
    return value


def serialized(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def bounded_document(result: dict[str, Any], limit: int, rows_key: str) -> bytes:
    """Bound metadata and diagnostics too, preserving explicit omission counts."""
    if limit < 128:
        raise ValueError("the minimum serialized response budget is 128 bytes")
    result = presentation(result)
    previously_omitted_rows = result.get("omitted_row_count", 0)
    original_size = len(serialized(result))
    if original_size <= limit:
        return serialized(result)
    omitted = {"rows": 0, "diagnostics": 0, "bytes": 0}
    result["output_omitted"] = omitted
    pools = [(key, "diagnostics") for key in ("malformed", "unsupported", "selection_errors", "errors")]
    pools.append((rows_key, "rows"))
    for key, category in pools:
        values = result.get(key, [])
        while values and len(serialized(result)) > limit:
            removed = values.pop()
            omitted[category] += 1
            omitted["bytes"] += len(serialized(removed))
    if rows_key == "matched_rows":
        result["emitted_row_count"] = len(result.get(rows_key, []))
        result["omitted_row_count"] = result.get("omitted_row_count", 0) + omitted["rows"]
    encoded = serialized(result)
    if len(encoded) <= limit:
        return encoded
    rows = previously_omitted_rows + omitted["rows"] + len(result.get(rows_key, []))
    diagnostics = omitted["diagnostics"] + sum(len(result.get(key, [])) for key, _ in pools[:-1])
    # A compact full-omission form also fits the minimum supported 128-byte budget.
    return serialized({"status": result.get("status", "error"), "omitted": [rows, diagnostics, original_size]})
