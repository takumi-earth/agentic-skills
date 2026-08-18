#!/usr/bin/env python3
"""Extract nested tools.update_goal calls from Codex rollout JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterator


TARGET = "tools.update_goal"
STATUS = re.compile(r"\bstatus\s*:\s*(['\"])(complete|blocked)\1")


class ExtractError(Exception):
    """Describe malformed rollout evidence."""


def skip_quoted(source: str, index: int, quote: str) -> int:
    """Return the first index after one JavaScript quoted region."""

    index += 1
    while index < len(source):
        if source[index] == "\\":
            index += 2
        elif source[index] == quote:
            return index + 1
        else:
            index += 1
    return index


def skip_comment(source: str, index: int) -> int:
    """Return the first index after a JavaScript comment."""

    if source.startswith("//", index):
        newline = source.find("\n", index + 2)
        return len(source) if newline < 0 else newline + 1
    if source.startswith("/*", index):
        end = source.find("*/", index + 2)
        return len(source) if end < 0 else end + 2
    return index


def balanced_call(source: str, opening: int) -> tuple[str, int] | None:
    """Return call contents and end position for one balanced parenthesis."""

    depth = 1
    index = opening + 1
    start = index
    while index < len(source):
        character = source[index]
        if character in "'\"`":
            index = skip_quoted(source, index, character)
            continue
        skipped = skip_comment(source, index)
        if skipped != index:
            index = skipped
            continue
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return source[start:index], index + 1
        index += 1
    return None


def nested_statuses(source: str) -> Iterator[str]:
    """Yield goal statuses from real calls outside strings and comments."""

    index = 0
    while index < len(source):
        character = source[index]
        if character in "'\"`":
            index = skip_quoted(source, index, character)
            continue
        skipped = skip_comment(source, index)
        if skipped != index:
            index = skipped
            continue
        if source.startswith(TARGET, index):
            before_ok = index == 0 or not (source[index - 1].isalnum() or source[index - 1] in "_$.")
            after = index + len(TARGET)
            after_ok = after == len(source) or not (source[after].isalnum() or source[after] in "_$")
            cursor = after
            while cursor < len(source) and source[cursor].isspace():
                cursor += 1
            if before_ok and after_ok and cursor < len(source) and source[cursor] == "(":
                balanced = balanced_call(source, cursor)
                if balanced is not None:
                    contents, index = balanced
                    match = STATUS.search(contents)
                    if match is not None:
                        yield match.group(2)
                    continue
        index += 1


def text_fragments(value: Any) -> Iterator[str]:
    """Yield string leaves from a typed tool output."""

    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from text_fragments(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from text_fragments(item)


def extract(path: Path) -> dict[str, Any]:
    """Extract and correlate nested lifecycle events."""

    calls: list[dict[str, Any]] = []
    outputs: dict[str, str] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as error:
                raise ExtractError(f"malformed JSON at line {line_number}: {error}") from error
            if record.get("type") != "response_item" or not isinstance(record.get("payload"), dict):
                continue
            payload = record["payload"]
            if payload.get("type") == "custom_tool_call_output" and isinstance(payload.get("call_id"), str):
                outputs[payload["call_id"]] = "\n".join(text_fragments(payload.get("output")))
                continue
            if payload.get("type") != "custom_tool_call" or payload.get("name") != "exec":
                continue
            if payload.get("status") != "completed" or not isinstance(payload.get("input"), str):
                continue
            call_id = payload.get("call_id")
            if not isinstance(call_id, str):
                continue
            for status in nested_statuses(payload["input"]):
                calls.append({"call_id": call_id, "line": line_number, "status": status})
    events: list[dict[str, Any]] = []
    for call in calls:
        expected = re.compile(rf'"status"\s*:\s*"{re.escape(call["status"])}"')
        output = outputs.get(call["call_id"], "")
        events.append({**call, "output_confirms": expected.search(output) is not None})
    return {"events": events, "schema_version": 1}


def main() -> int:
    """Parse arguments and emit lifecycle observations."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcript", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        report = extract(arguments.transcript)
    except (OSError, UnicodeError, ExtractError) as error:
        print(f"nested goal extraction failed: {error}", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
