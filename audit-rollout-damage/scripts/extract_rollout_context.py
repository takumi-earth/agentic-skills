#!/usr/bin/env python3
"""Extract deterministic, bounded context packets around selected rollout events."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from damage_common import (
    AssessmentInputError,
    atomic_write_text,
    canonical_json,
    display_path,
    load_json,
    load_jsonl,
    normalize_home_text,
    require_exact_keys,
    require_list,
    require_object,
    require_string,
    require_unique,
    sha256_bytes,
    sha256_file,
)


CALL_TYPES = {"function_call", "custom_tool_call"}
OUTPUT_TYPES = {"function_call_output", "custom_tool_call_output"}


def parse_args() -> argparse.Namespace:
    """Parse explicitly selected rollouts, one selection document, and one output."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", action="append", required=True, type=Path)
    parser.add_argument("--selection", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def normalized_text(value: str) -> str:
    """Normalize current-home paths without otherwise rewriting trace text."""
    return normalize_home_text(value)


def content_text(value: Any) -> str | None:
    """Extract visible text from one message or reasoning content value."""
    if isinstance(value, str):
        return value if value else None
    if not isinstance(value, list):
        return None
    parts: list[str] = []
    for item in value:
        if isinstance(item, str):
            parts.append(item)
            continue
        if not isinstance(item, dict):
            continue
        for key in ("text", "content"):
            text = item.get(key)
            if isinstance(text, str) and text:
                parts.append(text)
                break
    return "\n".join(parts) if parts else None


def call_identifier(payload: dict[str, Any]) -> str | None:
    """Return one call identifier from a call or output payload."""
    for key in ("call_id", "id"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def visible_payload_text(payload: dict[str, Any]) -> str | None:
    """Extract visible message, reasoning-summary, call-input, or output text."""
    payload_type = payload.get("type")
    if payload_type == "message":
        return content_text(payload.get("content"))
    if payload_type == "reasoning":
        return content_text(payload.get("summary")) or content_text(payload.get("content"))
    if payload_type in CALL_TYPES:
        value = payload.get("input", payload.get("arguments"))
    elif payload_type in OUTPUT_TYPES:
        value = payload.get("output")
    else:
        return None
    if isinstance(value, str):
        return value
    if value is None:
        return None
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def event_kind(payload_type: str) -> str:
    """Map trace payload types to stable context-event kinds."""
    if payload_type == "message":
        return "message"
    if payload_type == "reasoning":
        return "reasoning_summary"
    if payload_type in CALL_TYPES:
        return "tool_call"
    return "tool_output"


def origin_hint(payload: dict[str, Any], text: str) -> str | None:
    """Describe observable message provenance without deciding its authority."""
    if payload.get("type") != "message":
        return None
    role = payload.get("role")
    if role == "user" and text.lstrip().startswith("<codex_internal_context"):
        return "harness_internal_goal_context"
    if role == "user":
        return "direct_user_message"
    if role == "assistant":
        return "assistant_message"
    return "other_message"


def normalize_event(record: dict[str, Any], ordinal: int, maximum: int) -> dict[str, Any] | None:
    """Normalize one visible semantic response item."""
    if record.get("type") != "response_item":
        return None
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return None
    payload_type = payload.get("type")
    if payload_type not in {"message", "reasoning", *CALL_TYPES, *OUTPUT_TYPES}:
        return None
    raw_text = visible_payload_text(payload)
    if raw_text is None:
        return None
    text = normalized_text(raw_text)
    excerpt = text if len(text) <= maximum else f"{text[:maximum]}…"
    return {
        "ordinal": ordinal,
        "timestamp": record.get("timestamp"),
        "kind": event_kind(str(payload_type)),
        "payload_type": payload_type,
        "role": payload.get("role"),
        "origin_hint": origin_hint(payload, text),
        "name": payload.get("name"),
        "call_id": call_identifier(payload),
        "text_length": len(text),
        "text_sha256": sha256_bytes(text.encode("utf-8")),
        "text_excerpt": excerpt,
        "truncated": len(text) > maximum,
    }


def session_rollout_id(records: list[dict[str, Any]]) -> str | None:
    """Return the first declared rollout identifier."""
    for record in records:
        if record.get("type") != "session_meta":
            continue
        payload = record.get("payload")
        if isinstance(payload, dict) and isinstance(payload.get("id"), str):
            return payload["id"]
    return None


def nonnegative_integer(value: Any, location: str) -> int:
    """Validate one nonnegative integer."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise AssessmentInputError(f"{location}: expected nonnegative integer")
    return value


def positive_integer(value: Any, location: str) -> int:
    """Validate one positive integer."""
    result = nonnegative_integer(value, location)
    if result == 0:
        raise AssessmentInputError(f"{location}: expected positive integer")
    return result


def resolve_anchor(
    anchor: dict[str, Any],
    session_index: int,
    records: list[dict[str, Any]],
    semantic: list[dict[str, Any]],
    location: str,
) -> tuple[int, str | None]:
    """Resolve exactly one ordinal or call-ID anchor."""
    has_ordinal = "ordinal" in anchor
    has_call_id = "call_id" in anchor
    if has_ordinal == has_call_id:
        raise AssessmentInputError(f"{location}: provide exactly one of `ordinal` or `call_id`")
    if has_ordinal:
        ordinal = nonnegative_integer(anchor["ordinal"], f"{location}.ordinal")
        if ordinal >= len(records):
            raise AssessmentInputError(f"{location}.ordinal: outside session {session_index}")
        return ordinal, None
    identifier = require_string(anchor["call_id"], f"{location}.call_id")
    matches = [event for event in semantic if event.get("call_id") == identifier and event["kind"] == "tool_call"]
    if len(matches) != 1:
        raise AssessmentInputError(f"{location}.call_id: expected one call, found {len(matches)}")
    return int(matches[0]["ordinal"]), identifier


def selected_context(
    semantic: list[dict[str, Any]], anchor_ordinal: int, before: int, after: int, call_id: str | None
) -> list[dict[str, Any]]:
    """Select a bounded semantic window plus every correlated call event."""
    preceding = [event for event in semantic if event["ordinal"] < anchor_ordinal]
    following = [event for event in semantic if event["ordinal"] > anchor_ordinal]
    selected = preceding[-before:] if before else []
    selected += [event for event in semantic if event["ordinal"] == anchor_ordinal]
    selected += following[:after] if after else []
    if call_id is not None:
        selected += [event for event in semantic if event.get("call_id") == call_id]
    by_ordinal = {int(event["ordinal"]): event for event in selected}
    return [by_ordinal[ordinal] for ordinal in sorted(by_ordinal)]


def main() -> int:
    """Write deterministic context packets for explicitly selected anchors."""
    arguments = parse_args()
    try:
        selection_path = arguments.selection.expanduser().resolve(strict=True)
        selection = require_object(load_json(selection_path), "selection")
        require_exact_keys(selection, {"schema_version", "defaults", "anchors"}, set(), "selection")
        if selection["schema_version"] != 1:
            raise AssessmentInputError("selection.schema_version: expected 1")
        defaults = require_object(selection["defaults"], "selection.defaults")
        require_exact_keys(defaults, {"before", "after", "max_excerpt_chars"}, set(), "selection.defaults")
        default_before = nonnegative_integer(defaults["before"], "selection.defaults.before")
        default_after = nonnegative_integer(defaults["after"], "selection.defaults.after")
        maximum = positive_integer(defaults["max_excerpt_chars"], "selection.defaults.max_excerpt_chars")

        session_documents: list[dict[str, Any]] = []
        session_records: list[list[dict[str, Any]]] = []
        semantic_events: list[list[dict[str, Any]]] = []
        for session_index, source in enumerate(arguments.session):
            path = source.expanduser().resolve(strict=True)
            records = load_jsonl(path)
            semantic = [
                event
                for ordinal, record in enumerate(records)
                if (event := normalize_event(record, ordinal, maximum)) is not None
            ]
            session_records.append(records)
            semantic_events.append(semantic)
            session_documents.append(
                {
                    "session_index": session_index,
                    "session": display_path(path),
                    "session_sha256": sha256_file(path),
                    "rollout_id": session_rollout_id(records),
                    "record_count": len(records),
                    "semantic_event_count": len(semantic),
                }
            )

        anchor_values = require_list(selection["anchors"], "selection.anchors")
        if not anchor_values:
            raise AssessmentInputError("selection.anchors: expected at least one anchor")
        anchors: list[dict[str, Any]] = []
        identifiers: list[str] = []
        for index, anchor_value in enumerate(anchor_values):
            location = f"selection.anchors[{index}]"
            anchor = require_object(anchor_value, location)
            require_exact_keys(
                anchor,
                {"id", "session_index"},
                {"ordinal", "call_id", "before", "after"},
                location,
            )
            identifier = require_string(anchor["id"], f"{location}.id")
            identifiers.append(identifier)
            session_index = nonnegative_integer(anchor["session_index"], f"{location}.session_index")
            if session_index >= len(session_records):
                raise AssessmentInputError(f"{location}.session_index: unknown session {session_index}")
            before = nonnegative_integer(anchor.get("before", default_before), f"{location}.before")
            after = nonnegative_integer(anchor.get("after", default_after), f"{location}.after")
            ordinal, requested_call_id = resolve_anchor(
                anchor,
                session_index,
                session_records[session_index],
                semantic_events[session_index],
                location,
            )
            anchor_event = next((event for event in semantic_events[session_index] if event["ordinal"] == ordinal), None)
            if anchor_event is None:
                raise AssessmentInputError(f"{location}: selected ordinal has no visible semantic event")
            correlated_call_id = requested_call_id or anchor_event.get("call_id")
            anchors.append(
                {
                    "id": identifier,
                    "session_index": session_index,
                    "rollout_id": session_documents[session_index]["rollout_id"],
                    "anchor_ordinal": ordinal,
                    "anchor_kind": anchor_event["kind"],
                    "call_id": correlated_call_id,
                    "before": before,
                    "after": after,
                    "events": selected_context(
                        semantic_events[session_index], ordinal, before, after, correlated_call_id
                    ),
                }
            )
        require_unique(identifiers, "selection.anchors")
        result = {
            "schema_version": 1,
            "selection": {"path": display_path(selection_path), "sha256": sha256_file(selection_path)},
            "sessions": session_documents,
            "anchors": anchors,
        }
        atomic_write_text(arguments.output.expanduser(), canonical_json(result))
    except (AssessmentInputError, OSError) as error:
        raise SystemExit(str(error)) from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
