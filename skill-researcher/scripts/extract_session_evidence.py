#!/usr/bin/env python3
"""Extract bounded, visible evidence from one Codex rollout session."""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


SKILL_REF_RE = re.compile(r"\$([a-z0-9][a-z0-9:-]{0,127})")
DECLARED_USE_RE = re.compile(
    r"(?i)\b(?:apply|applying|follow|following|invoke|invoking|use|using)\b"
)
NEGATED_DECLARED_USE_RE = re.compile(
    r"(?i)(?:\b(?:do|does|did|will|would|should|can|could|must)\s+not\b|"
    r"\b(?:don't|doesn't|didn't|won't|wouldn't|shouldn't|can't|couldn't|"
    r"mustn't|never)\b)[^.!?\n]{0,32}$"
)
DECLARED_USE_SEPARATOR_RE = re.compile(r"[.!?;\n]")
FAILURE_RE = re.compile(
    r"(?i)(?:\berror\b|\bfailed\b|\bfailure\b|\bdenied\b|\btimed out\b|"
    r"\bexit(?:ed)?(?: code|_code)?\s*[:=]?\s*[1-9]\d*\b|"
    r'"exit_code"\s*:\s*[1-9]\d*)'
)


@dataclass
class SkillInfo:
    name: str
    path: Path
    owner: str
    signals: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Message:
    line: int
    timestamp: str | None
    role: str
    phase: str | None
    text: str
    skill_refs: list[str]
    preceding_calls: list[dict[str, Any]] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract visible, bounded session evidence, goal events, tool leads, "
            "and skill-use signals from a Codex rollout JSONL file."
        )
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--transcript", type=Path, help="Absolute rollout JSONL path")
    source.add_argument("--session-id", help="Codex session/thread UUID")
    parser.add_argument(
        "--sessions-root",
        type=Path,
        default=Path.home() / ".codex" / "sessions",
        help="Session tree used with --session-id",
    )
    parser.add_argument(
        "--skills-root",
        type=Path,
        default=Path.home() / ".codex" / "skills",
        help="User-level Codex skill root",
    )
    parser.add_argument(
        "--max-message-chars",
        type=int,
        default=4_000,
        help="Maximum characters retained from one visible message",
    )
    parser.add_argument(
        "--max-total-message-chars",
        type=int,
        default=90_000,
        help="Maximum characters retained across selected visible messages",
    )
    parser.add_argument(
        "--max-tool-output-chars",
        type=int,
        default=1_200,
        help="Maximum characters retained from one candidate failing tool output",
    )
    parser.add_argument(
        "--exclude-skill",
        action="append",
        default=[],
        help="Skill name to exclude from the user-owned used-skill shortlist",
    )
    return parser.parse_args()


def read_frontmatter_name(path: Path) -> str | None:
    try:
        with path.open(encoding="utf-8") as handle:
            if handle.readline().strip() != "---":
                return None
            for line in handle:
                stripped = line.strip()
                if stripped == "---":
                    return None
                if stripped.startswith("name:"):
                    value = stripped.partition(":")[2].strip().strip("\"'")
                    return value or None
    except OSError:
        return None
    return None


def discover_skills(root: Path) -> dict[str, SkillInfo]:
    skills: dict[str, SkillInfo] = {}
    if not root.is_dir():
        return skills

    for skill_file in sorted(root.glob("*/SKILL.md")):
        name = read_frontmatter_name(skill_file)
        if not name:
            continue
        skills[name] = SkillInfo(
            name=name,
            path=skill_file,
            owner="user",
        )

    system_root = root / ".system"
    if system_root.is_dir():
        for skill_file in sorted(system_root.glob("*/SKILL.md")):
            name = read_frontmatter_name(skill_file)
            if not name:
                continue
            skills.setdefault(
                name,
                SkillInfo(
                    name=name,
                    path=skill_file,
                    owner="system",
                ),
            )
    return skills


def resolve_transcript(args: argparse.Namespace) -> Path:
    if args.transcript is not None:
        path = args.transcript.expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"transcript is not a file: {path}")
        return path

    session_id = args.session_id
    assert session_id is not None
    root = args.sessions_root.expanduser().resolve()
    matches = sorted(root.rglob(f"*{session_id}*.jsonl"))
    if not matches:
        raise FileNotFoundError(
            f"no rollout JSONL filename under {root} contains session ID {session_id}"
        )
    if len(matches) > 1:
        rendered = "\n".join(f"- {match}" for match in matches)
        raise RuntimeError(
            f"multiple rollout files matched session ID {session_id}:\n{rendered}"
        )
    return matches[0].resolve()


def truncate(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    omitted = len(text) - limit
    return f"{text[:limit]}\n...[{omitted} characters omitted]", True


def compact_goal(goal: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in (
        "goalId",
        "goal_id",
        "threadId",
        "thread_id",
        "status",
        "tokensUsed",
        "tokens_used",
        "tokenBudget",
        "token_budget",
        "timeUsedSeconds",
        "time_used_seconds",
        "createdAt",
        "created_at",
        "updatedAt",
        "updated_at",
    ):
        if goal.get(key) is not None:
            result[key] = goal[key]
    objective = goal.get("objective")
    if isinstance(objective, str):
        result["objective"], result["objective_truncated"] = truncate(objective, 6_000)
    return result


def content_text(content: Any) -> str:
    if not isinstance(content, list):
        return ""
    chunks: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") not in {"input_text", "output_text", "text"}:
            continue
        value = block.get("text")
        if isinstance(value, str):
            chunks.append(value)
    return "\n".join(chunks)


def decode_json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def flatten_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from flatten_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from flatten_strings(nested)


def tool_call_summary(payload: dict[str, Any], limit: int = 300) -> str:
    raw = payload.get("arguments")
    if raw is None:
        raw = payload.get("input")
    if raw is None:
        return ""
    if not isinstance(raw, str):
        raw = json.dumps(raw, ensure_ascii=False, sort_keys=True)
    compact = " ".join(raw.split())
    return truncate(compact, limit)[0]


def add_skill_signal(
    skills: dict[str, SkillInfo],
    name: str,
    *,
    kind: str,
    line: int,
    timestamp: str | None,
    detail: str,
) -> None:
    skill = skills.get(name)
    if skill is None:
        return
    signal = {
        "kind": kind,
        "line": line,
        "timestamp": timestamp,
        "detail": detail,
    }
    if signal not in skill.signals:
        skill.signals.append(signal)


def skill_reads_from_text(text: str, skills: dict[str, SkillInfo]) -> list[str]:
    normalized = text.replace("\\/", "/")
    if "SKILL.md" not in normalized:
        return []
    found: list[str] = []
    for name, skill in skills.items():
        path_text = str(skill.path)
        if path_text in normalized:
            found.append(name)
            continue
        if (
            "/.codex/skills/" in normalized
            and re.search(rf"(?<![a-z0-9-]){re.escape(name)}(?![a-z0-9-])", normalized)
            and "SKILL.md" in normalized
        ):
            found.append(name)
    return sorted(set(found))


def user_invoked_skill_refs(text: str, skills: dict[str, SkillInfo]) -> list[str]:
    invocation_region = text[:1_000]
    return sorted(
        {name for name in SKILL_REF_RE.findall(invocation_region) if name in skills}
    )


def assistant_declared_skill_refs(text: str, skills: dict[str, SkillInfo]) -> list[str]:
    found: set[str] = set()
    for name in skills:
        mention_re = re.compile(
            rf"(?<![a-z0-9:-])(?:\${re.escape(name)}|`{re.escape(name)}`|"
            rf"{re.escape(name)})(?![a-z0-9:-])"
        )
        for match in mention_re.finditer(text):
            prefix = text[max(0, match.start() - 140) : match.start()]
            declared_uses = list(DECLARED_USE_RE.finditer(prefix))
            if not declared_uses:
                continue
            declared_use = declared_uses[-1]
            if DECLARED_USE_SEPARATOR_RE.search(prefix[declared_use.end() :]):
                continue
            negation_prefix = prefix[
                max(0, declared_use.start() - 48) : declared_use.start()
            ]
            if NEGATED_DECLARED_USE_RE.search(negation_prefix):
                continue
            found.add(name)
            break
    return sorted(found)


def mark_preceding_assistants(messages: list[Message]) -> set[int]:
    selected: set[int] = set()
    last_assistant_index: int | None = None
    for index, message in enumerate(messages):
        if message.role == "assistant":
            last_assistant_index = index
        elif message.role == "user" and last_assistant_index is not None:
            selected.add(last_assistant_index)
    return selected


def select_messages(
    messages: list[Message],
    *,
    max_message_chars: int,
    max_total_chars: int,
) -> tuple[list[dict[str, Any]], bool]:
    preceding = mark_preceding_assistants(messages)
    priorities: list[tuple[int, int]] = []
    first_user_index = next(
        (index for index, message in enumerate(messages) if message.role == "user"),
        None,
    )
    for index, message in enumerate(messages):
        priority = 10
        if message.role == "user":
            priority = 120 if index == first_user_index else 110
        if message.phase == "final_answer":
            priority = max(priority, 105)
        if index in preceding:
            priority = max(priority, 90)
        if message.skill_refs:
            priority = max(priority, 85)
        priorities.append((priority, index))

    kept: set[int] = set()
    consumed = 0
    any_truncated = False
    for _, index in sorted(priorities, key=lambda pair: (-pair[0], pair[1])):
        message = messages[index]
        bounded, was_truncated = truncate(message.text, max_message_chars)
        cost = len(bounded)
        if consumed + cost > max_total_chars and kept:
            any_truncated = True
            continue
        kept.add(index)
        consumed += cost
        any_truncated = any_truncated or was_truncated

    result: list[dict[str, Any]] = []
    for index in sorted(kept):
        message = messages[index]
        bounded, was_truncated = truncate(message.text, max_message_chars)
        result.append(
            {
                "line": message.line,
                "timestamp": message.timestamp,
                "role": message.role,
                "phase": message.phase,
                "text": bounded,
                "text_truncated": was_truncated,
                "skill_refs": message.skill_refs,
                "preceding_tool_calls": message.preceding_calls,
            }
        )
    return result, any_truncated or len(kept) != len(messages)


def extract(args: argparse.Namespace) -> dict[str, Any]:
    transcript = resolve_transcript(args)
    skills = discover_skills(args.skills_root.expanduser().resolve())

    messages: list[Message] = []
    tool_counts: collections.Counter[str] = collections.Counter()
    recent_calls: collections.deque[dict[str, Any]] = collections.deque(maxlen=3)
    calls_by_id: dict[str, dict[str, Any]] = {}
    goal_events: list[dict[str, Any]] = []
    failure_candidates: list[dict[str, Any]] = []
    session_meta: dict[str, Any] = {}
    turn_ids: set[str] = set()
    malformed_lines: list[int] = []
    live_user_texts: collections.Counter[str] = collections.Counter()
    live_user_skill_refs: dict[str, set[str]] = collections.defaultdict(set)
    total_lines = 0
    first_timestamp: str | None = None
    last_timestamp: str | None = None

    with transcript.open(encoding="utf-8", errors="replace") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            total_lines = line_no
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError:
                malformed_lines.append(line_no)
                continue
            if not isinstance(record, dict):
                continue

            timestamp = record.get("timestamp")
            if isinstance(timestamp, str):
                first_timestamp = first_timestamp or timestamp
                last_timestamp = timestamp

            record_type = record.get("type")
            payload = record.get("payload")
            if not isinstance(payload, dict):
                continue

            if record_type == "session_meta":
                session_meta = {
                    key: payload.get(key)
                    for key in (
                        "id",
                        "session_id",
                        "cwd",
                        "originator",
                        "source",
                        "cli_version",
                        "model_provider",
                    )
                    if payload.get(key) is not None
                }
                continue

            if record_type == "turn_context":
                turn_id = payload.get("turn_id")
                if isinstance(turn_id, str):
                    turn_ids.add(turn_id)
                continue

            if record_type == "event_msg":
                event_type = payload.get("type")
                if event_type == "user_message":
                    message_text = payload.get("message")
                    if isinstance(message_text, str):
                        normalized_message = message_text.strip()
                        live_user_texts[normalized_message] += 1
                        text_elements = payload.get("text_elements")
                        if isinstance(text_elements, list):
                            for element in text_elements:
                                if not isinstance(element, dict):
                                    continue
                                placeholder = element.get("placeholder")
                                if not isinstance(placeholder, str):
                                    continue
                                match = SKILL_REF_RE.fullmatch(placeholder)
                                if match and match.group(1) in skills:
                                    live_user_skill_refs[normalized_message].add(
                                        match.group(1)
                                    )
                    continue
                if event_type == "thread_goal_updated":
                    goal = payload.get("goal")
                    if isinstance(goal, dict):
                        goal_events.append(
                            {
                                "kind": "thread_goal_updated",
                                "line": line_no,
                                "timestamp": timestamp,
                                "goal": compact_goal(goal),
                            }
                        )
                    continue

            if record_type != "response_item":
                continue

            payload_type = payload.get("type")
            if payload_type == "message":
                role = payload.get("role")
                if role not in {"user", "assistant"}:
                    continue
                text = content_text(payload.get("content"))
                if not text:
                    continue
                refs = (
                    user_invoked_skill_refs(text, skills)
                    if role == "user"
                    else assistant_declared_skill_refs(text, skills)
                )
                if role == "assistant":
                    for name in refs:
                        add_skill_signal(
                            skills,
                            name,
                            kind="assistant_declared_use",
                            line=line_no,
                            timestamp=timestamp,
                            detail=truncate(" ".join(text.split()), 300)[0],
                        )
                messages.append(
                    Message(
                        line=line_no,
                        timestamp=timestamp if isinstance(timestamp, str) else None,
                        role=role,
                        phase=payload.get("phase")
                        if isinstance(payload.get("phase"), str)
                        else None,
                        text=text,
                        skill_refs=refs,
                        preceding_calls=list(recent_calls) if role == "user" else [],
                    )
                )
                continue

            if payload_type in {"function_call", "custom_tool_call"}:
                name = payload.get("name")
                if not isinstance(name, str):
                    name = "<unknown>"
                tool_counts[name] += 1
                call_id = payload.get("call_id")
                summary = tool_call_summary(payload)
                call = {
                    "line": line_no,
                    "timestamp": timestamp,
                    "name": name,
                    "summary": summary,
                }
                recent_calls.append(call)
                if isinstance(call_id, str):
                    calls_by_id[call_id] = call

                for text_value in flatten_strings(
                    [payload.get("arguments"), payload.get("input")]
                ):
                    for skill_name in skill_reads_from_text(text_value, skills):
                        add_skill_signal(
                            skills,
                            skill_name,
                            kind="skill_file_read",
                            line=line_no,
                            timestamp=timestamp,
                            detail=f"{name}: {summary}",
                        )

                if name in {"create_goal", "get_goal", "update_goal"}:
                    arguments = decode_json_object(payload.get("arguments"))
                    goal_events.append(
                        {
                            "kind": "goal_tool_call",
                            "line": line_no,
                            "timestamp": timestamp,
                            "tool": name,
                            "arguments": arguments,
                            "call_id": call_id,
                        }
                    )
                continue

            if payload_type in {
                "function_call_output",
                "custom_tool_call_output",
            }:
                call_id = payload.get("call_id")
                call = calls_by_id.get(call_id) if isinstance(call_id, str) else None
                output = payload.get("output")
                if output is None:
                    output = payload.get("result")
                if not isinstance(output, str):
                    output = json.dumps(output, ensure_ascii=False, sort_keys=True)

                if call and call["name"] in {"create_goal", "get_goal", "update_goal"}:
                    parsed_output = decode_json_object(output)
                    compact_output: dict[str, Any] | str
                    if parsed_output:
                        compact_output = {
                            key: value
                            for key, value in parsed_output.items()
                            if key not in {"goal", "completionBudgetReport"}
                        }
                        parsed_goal = decode_json_object(parsed_output.get("goal"))
                        if parsed_goal:
                            compact_output["goal"] = compact_goal(parsed_goal)
                        report = parsed_output.get("completionBudgetReport")
                        if isinstance(report, str):
                            compact_output["completionBudgetReport"] = truncate(
                                report, 2_000
                            )[0]
                    else:
                        compact_output = truncate(output, 2_500)[0]
                    goal_events.append(
                        {
                            "kind": "goal_tool_output",
                            "line": line_no,
                            "timestamp": timestamp,
                            "tool": call["name"],
                            "call_line": call["line"],
                            "call_id": call_id,
                            "output": compact_output,
                        }
                    )

                if output and FAILURE_RE.search(output):
                    bounded, was_truncated = truncate(
                        output, args.max_tool_output_chars
                    )
                    failure_candidates.append(
                        {
                            "line": line_no,
                            "timestamp": timestamp,
                            "tool": call["name"] if call else "<unknown>",
                            "call_line": call["line"] if call else None,
                            "output": bounded,
                            "output_truncated": was_truncated,
                            "heuristic_only": True,
                        }
                    )

    live_user_filter_applied = bool(live_user_texts)
    if live_user_filter_applied:
        messages = [
            message
            for message in messages
            if message.role != "user" or live_user_texts[message.text.strip()] > 0
        ]

    for message in messages:
        if message.role != "user":
            continue
        structured_refs = live_user_skill_refs.get(message.text.strip())
        if structured_refs:
            message.skill_refs = sorted(structured_refs)
        for name in message.skill_refs:
            add_skill_signal(
                skills,
                name,
                kind="explicit_invocation",
                line=message.line,
                timestamp=message.timestamp,
                detail=truncate(" ".join(message.text.split()), 300)[0],
            )

    selected_messages, messages_truncated = select_messages(
        messages,
        max_message_chars=args.max_message_chars,
        max_total_chars=args.max_total_message_chars,
    )

    used_skills: list[dict[str, Any]] = []
    excluded_skills = set(args.exclude_skill)
    for skill in sorted(skills.values(), key=lambda item: item.name):
        signal_kinds = {signal["kind"] for signal in skill.signals}
        used = "skill_file_read" in signal_kinds and bool(
            {"explicit_invocation", "assistant_declared_use"} & signal_kinds
        )
        if not used:
            continue
        used_skills.append(
            {
                "name": skill.name,
                "path": str(skill.path),
                "owner": skill.owner,
                "excluded_by_request": skill.name in excluded_skills,
                "signals": skill.signals,
            }
        )

    user_owned_names = [
        skill["name"]
        for skill in used_skills
        if skill["owner"] == "user" and not skill["excluded_by_request"]
    ]
    complete_outputs = [
        event
        for event in goal_events
        if event.get("kind") == "goal_tool_output"
        and event.get("tool") == "update_goal"
        and (
            isinstance(event.get("output"), dict)
            and decode_json_object(event["output"].get("goal")).get("status")
            == "complete"
        )
    ]

    return {
        "schema_version": 1,
        "evidence_contract": {
            "visible_messages_only": True,
            "reasoning_excluded": True,
            "system_and_developer_messages_excluded": True,
            "live_user_event_filter_applied": live_user_filter_applied,
            "skill_and_failure_detection_is_heuristic": True,
            "raw_transcript_is_authoritative": True,
        },
        "transcript": {
            "path": str(transcript),
            "total_lines": total_lines,
            "malformed_lines": malformed_lines,
            "first_timestamp": first_timestamp,
            "last_timestamp": last_timestamp,
            "session_meta": session_meta,
            "turn_ids": sorted(turn_ids),
        },
        "goal_context": {
            "successful_completion_detected": bool(complete_outputs),
            "completion_outputs": complete_outputs,
            "events": goal_events,
        },
        "skills": {
            "root": str(args.skills_root.expanduser().resolve()),
            "used": used_skills,
            "user_owned_used_skill_names": user_owned_names,
            "excluded_skill_names": sorted(excluded_skills),
        },
        "visible_messages": {
            "selected_count": len(selected_messages),
            "total_count": len(messages),
            "truncated": messages_truncated,
            "items": selected_messages,
        },
        "tools": {
            "counts": dict(sorted(tool_counts.items())),
            "failure_candidates": failure_candidates[:20],
            "failure_candidates_total": len(failure_candidates),
            "failure_candidates_truncated": len(failure_candidates) > 20,
        },
    }


def main() -> int:
    args = parse_args()
    if (
        args.max_message_chars < 1
        or args.max_total_message_chars < 1
        or args.max_tool_output_chars < 1
    ):
        print("error: all output bounds must be positive", file=sys.stderr)
        return 2
    try:
        result = extract(args)
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
