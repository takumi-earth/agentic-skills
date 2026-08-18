#!/usr/bin/env python3
"""Merge transcript lifecycle observations with authoritative goal status."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


VALID_AUTHORITY = {"active", "blocked", "complete"}
VALID_EVENT = {"blocked", "complete"}


class MergeError(Exception):
    """Describe malformed or missing lifecycle evidence."""


def load_object(path: Path) -> dict[str, Any]:
    """Load one JSON object."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MergeError(f"expected a JSON object: {path}")
    return payload


def select_authority(payload: dict[str, Any], goal_id: str) -> dict[str, str]:
    """Select the latest uniquely timestamped authoritative record."""

    records = payload.get("records")
    if not isinstance(records, list):
        raise MergeError("authoritative source must contain a records array")
    matching: list[dict[str, str]] = []
    for raw in records:
        if not isinstance(raw, dict) or raw.get("goal_id") != goal_id:
            continue
        status = raw.get("status")
        observed_at = raw.get("observed_at")
        if status not in VALID_AUTHORITY or not isinstance(observed_at, str) or not observed_at:
            raise MergeError(f"invalid authoritative record for goal {goal_id}")
        matching.append({"goal_id": goal_id, "observed_at": observed_at, "status": status})
    if not matching:
        raise MergeError(f"no authoritative record for goal {goal_id}")
    matching.sort(key=lambda item: item["observed_at"])
    if len(matching) > 1 and matching[-1]["observed_at"] == matching[-2]["observed_at"]:
        raise MergeError(f"ambiguous latest authoritative record for goal {goal_id}")
    return matching[-1]


def normalize_events(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate normalized transcript event records."""

    events = payload.get("events")
    if not isinstance(events, list):
        raise MergeError("transcript source must contain an events array")
    normalized: list[dict[str, Any]] = []
    for raw in events:
        if not isinstance(raw, dict):
            raise MergeError("every transcript event must be an object")
        call_id = raw.get("call_id")
        line = raw.get("line")
        status = raw.get("status")
        confirms = raw.get("output_confirms")
        if not isinstance(call_id, str) or not isinstance(line, int) or status not in VALID_EVENT or not isinstance(confirms, bool):
            raise MergeError("malformed transcript event")
        normalized.append(
            {"call_id": call_id, "line": line, "output_confirms": confirms, "status": status}
        )
    return normalized


def main() -> int:
    """Merge both evidence sources and emit provenance-preserving JSON."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--goal-id", required=True)
    parser.add_argument("--transcript-events", type=Path, required=True)
    parser.add_argument("--authoritative", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        authority = select_authority(load_object(arguments.authoritative), arguments.goal_id)
        events = normalize_events(load_object(arguments.transcript_events))
    except (OSError, UnicodeError, json.JSONDecodeError, MergeError) as error:
        print(f"goal lifecycle merge failed: {error}", file=sys.stderr)
        return 2
    confirmed = [event for event in events if event["output_confirms"]]
    unconfirmed = [event for event in events if not event["output_confirms"]]
    disagreements = [event for event in confirmed if event["status"] != authority["status"]]
    report = {
        "authoritative": authority,
        "confirmed_transcript_events": confirmed,
        "current_status": authority["status"],
        "disagreements": disagreements,
        "goal_id": arguments.goal_id,
        "schema_version": 1,
        "unconfirmed_transcript_events": unconfirmed,
    }
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
