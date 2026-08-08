#!/usr/bin/env python3
"""Print compact visible context around selected JSONL source lines."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


INJECTED_BLOCK_RE = re.compile(
    r"(?is)<(?P<tag>system-reminder|local-command-caveat|local-command-stdout)>"
    r".*?</(?P=tag)>"
)


@dataclass
class Event:
    line: int
    role: str
    text: str


def content_text(content: Any, include_tools: bool) -> list[str]:
    if isinstance(content, str):
        return [content]
    if not isinstance(content, list):
        return []
    texts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type in {"text", "input_text", "output_text"}:
            text = block.get("text")
            if isinstance(text, str):
                texts.append(text)
        elif include_tools and block_type in {"tool_use", "tool_result"}:
            name = block.get("name", "<unknown>")
            texts.append(f"[{block_type}: {name}]")
    return texts


def codex_event(
    line: int,
    record: dict[str, Any],
    *,
    include_instructions: bool,
    include_tools: bool,
    include_meta: bool,
) -> Event | None:
    record_type = record.get("type")
    payload = record.get("payload")
    if not isinstance(payload, dict):
        if include_meta and record_type in {"compacted", "turn_context"}:
            return Event(line, "meta", f"[{record_type}]")
        return None
    payload_type = payload.get("type")
    if record_type == "response_item" and payload_type == "message":
        role = payload.get("role")
        allowed_roles = {"user", "assistant"}
        if include_instructions:
            allowed_roles.update({"developer", "system"})
        if role not in allowed_roles:
            return None
        text = "\n".join(content_text(payload.get("content"), include_tools)).strip()
        return Event(line, str(role), text) if text else None
    if (
        include_tools
        and record_type == "response_item"
        and payload_type in {"function_call", "custom_tool_call"}
    ):
        return Event(line, "tool", f"[tool call: {payload.get('name', '<unknown>')}]")
    if include_meta and record_type in {"compacted", "turn_context"}:
        return Event(line, "meta", f"[{record_type}]")
    return None


def claude_event(
    line: int,
    record: dict[str, Any],
    *,
    include_instructions: bool,
    include_tools: bool,
    include_meta: bool,
) -> Event | None:
    record_type = record.get("type")
    if record_type in {"user", "assistant"}:
        if record.get("isMeta") is True and not include_instructions:
            return None
        message = record.get("message")
        if not isinstance(message, dict):
            return None
        role = str(message.get("role") or record_type)
        if role in {"system", "developer"} and not include_instructions:
            return None
        text = "\n".join(content_text(message.get("content"), include_tools)).strip()
        return Event(line, role, text) if text else None
    if include_meta and record_type in {
        "system",
        "progress",
        "queue-operation",
        "file-history-snapshot",
    }:
        return Event(line, "meta", f"[{record_type}]")
    return None


def detect_harness(path: Path) -> str:
    parts = path.parts
    if ".codex" in parts:
        return "codex"
    if ".claude" in parts:
        return "claude"
    raise SystemExit(f"cannot infer harness from path: {path}")


def load_events(
    path: Path,
    harness: str,
    *,
    include_instructions: bool,
    include_tools: bool,
    include_meta: bool,
) -> tuple[list[Event], list[int]]:
    events: list[Event] = []
    malformed_lines: list[int] = []
    with path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            try:
                record = json.loads(raw_line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                malformed_lines.append(line_number)
                continue
            if not isinstance(record, dict):
                continue
            if harness == "codex":
                event = codex_event(
                    line_number,
                    record,
                    include_instructions=include_instructions,
                    include_tools=include_tools,
                    include_meta=include_meta,
                )
            else:
                event = claude_event(
                    line_number,
                    record,
                    include_instructions=include_instructions,
                    include_tools=include_tools,
                    include_meta=include_meta,
                )
            if event is not None:
                events.append(event)
    return events, malformed_lines


def compact_text(text: str, max_chars: int) -> str:
    text = INJECTED_BLOCK_RE.sub(" ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n[truncated]"


def select_context(
    events: list[Event], target_line: int, before: int, after: int
) -> list[Event]:
    if not events:
        return []
    target_index = min(
        range(len(events)), key=lambda index: abs(events[index].line - target_line)
    )
    start = max(0, target_index - before)
    end = min(len(events), target_index + after + 1)
    return events[start:end]


def parse_lines(value: str) -> list[int]:
    result: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        line = int(part)
        if line < 1:
            raise argparse.ArgumentTypeError("line numbers must be positive")
        result.append(line)
    if not result:
        raise argparse.ArgumentTypeError("at least one line number is required")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show bounded visible context around exact trace lines."
    )
    parser.add_argument("path", type=Path)
    parser.add_argument("--line", required=True, type=parse_lines)
    parser.add_argument("--harness", choices=("codex", "claude"))
    parser.add_argument("--before", type=int, default=3)
    parser.add_argument("--after", type=int, default=4)
    parser.add_argument("--max-chars", type=int, default=6_000)
    parser.add_argument("--include-instructions", action="store_true")
    parser.add_argument("--include-tools", action="store_true")
    parser.add_argument("--include-meta", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.before < 0 or args.after < 0:
        raise SystemExit("--before and --after must be nonnegative")
    if args.max_chars < 1:
        raise SystemExit("--max-chars must be positive")
    path = args.path.expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"trace is not a file: {path}")
    harness = args.harness or detect_harness(path)
    events, malformed_lines = load_events(
        path,
        harness,
        include_instructions=args.include_instructions,
        include_tools=args.include_tools,
        include_meta=args.include_meta,
    )
    if malformed_lines:
        rendered = ",".join(str(line) for line in malformed_lines[:20])
        suffix = "..." if len(malformed_lines) > 20 else ""
        print(f"Malformed JSONL lines skipped: `{rendered}{suffix}`")
        print()

    seen: set[tuple[int, str, str]] = set()
    for target_line in args.line:
        print(f"## Target line {target_line}")
        print()
        selected = select_context(events, target_line, args.before, args.after)
        if not selected:
            print("No visible events found.")
            print()
            continue
        for event in selected:
            identity = (event.line, event.role, event.text)
            if identity in seen:
                continue
            seen.add(identity)
            print(f"### `{event.role}` at line `{event.line}`")
            print()
            print(compact_text(event.text, args.max_chars))
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
