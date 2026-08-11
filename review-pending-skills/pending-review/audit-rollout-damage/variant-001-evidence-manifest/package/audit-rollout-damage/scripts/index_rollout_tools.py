#!/usr/bin/env python3
"""Index tool calls and correlated outputs from explicitly selected rollout JSONL files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from damage_common import AssessmentInputError, atomic_write_text, canonical_json, display_path, load_jsonl, sha256_file


TOOL_PAYLOAD_TYPES = {
    "function_call",
    "function_call_output",
    "custom_tool_call",
    "custom_tool_call_output",
}


def parse_args() -> argparse.Namespace:
    """Parse selected rollout inputs and one output path."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", action="append", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def compact(value: Any, limit: int = 2_000) -> str:
    """Serialize one value and cap only the convenience excerpt."""
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, ensure_ascii=False)
    return text if len(text) <= limit else f"{text[:limit]}…"


def call_id(payload: dict[str, Any]) -> str | None:
    """Return a normalized call identifier when present."""
    for key in ("call_id", "id"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def index_session(path: Path, session_index: int) -> dict[str, Any]:
    """Index one complete rollout without interpreting authority or effects."""
    records = load_jsonl(path)
    session_meta: dict[str, Any] | None = None
    tool_events: list[dict[str, Any]] = []
    by_id: dict[str, list[dict[str, Any]]] = {}
    uncorrelated: list[dict[str, Any]] = []

    for ordinal, record in enumerate(records):
        if record.get("type") == "session_meta" and session_meta is None:
            payload = record.get("payload")
            if isinstance(payload, dict):
                session_meta = payload
        if record.get("type") != "response_item":
            continue
        payload = record.get("payload")
        if not isinstance(payload, dict) or payload.get("type") not in TOOL_PAYLOAD_TYPES:
            continue
        identifier = call_id(payload)
        event = {
            "session_index": session_index,
            "ordinal": ordinal,
            "timestamp": record.get("timestamp"),
            "payload_type": payload.get("type"),
            "call_id": identifier,
            "name": payload.get("name"),
            "status": payload.get("status"),
            "input": payload.get("input", payload.get("arguments")),
            "output": payload.get("output"),
            "payload_keys": sorted(payload),
            "payload_excerpt": compact(payload),
        }
        tool_events.append(event)
        if identifier is None:
            uncorrelated.append(event)
        else:
            by_id.setdefault(identifier, []).append(event)

    correlations: list[dict[str, Any]] = []
    for identifier, events in sorted(by_id.items(), key=lambda item: item[1][0]["ordinal"]):
        calls = [event for event in events if not str(event["payload_type"]).endswith("_output")]
        outputs = [event for event in events if str(event["payload_type"]).endswith("_output")]
        correlations.append({"call_id": identifier, "call_events": calls, "output_events": outputs})

    rollout_id = None
    if session_meta is not None and isinstance(session_meta.get("id"), str):
        rollout_id = session_meta["id"]
    return {
        "session_index": session_index,
        "session": display_path(path),
        "session_sha256": sha256_file(path),
        "rollout_id": rollout_id,
        "records": len(records),
        "tool_events": tool_events,
        "correlations": correlations,
        "uncorrelated_tool_events": uncorrelated,
    }


def main() -> int:
    """Write the deterministic multi-session tool index."""
    arguments = parse_args()
    try:
        sessions = [index_session(path.expanduser(), index) for index, path in enumerate(arguments.session)]
        result = {"schema_version": 1, "sessions": sessions}
        atomic_write_text(arguments.output.expanduser(), canonical_json(result))
    except (AssessmentInputError, OSError) as error:
        raise SystemExit(str(error)) from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
