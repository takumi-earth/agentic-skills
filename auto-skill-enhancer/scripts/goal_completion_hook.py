#!/usr/bin/env python3
"""Inject the auto-skill-enhancer workflow after a goal completes."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from uuid import UUID


def object_value(value: Any) -> dict[str, Any]:
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


def referenced_goal_file(goal: dict[str, Any], codex_home: Path) -> Path | None:
    """Resolve the single managed attachment path exposed by `goal.objective`."""

    objective = goal.get("objective")
    if not isinstance(objective, str):
        return None

    attachments = (codex_home / "attachments").resolve()
    attachment_prefix = f"{attachments}/"
    referenced_dirs: set[Path] = set()
    search_from = 0
    while True:
        reference_start = objective.find(attachment_prefix, search_from)
        if reference_start < 0:
            break
        identifier_start = reference_start + len(attachment_prefix)
        attachment_id, separator, _ = objective[identifier_start:].partition("/")
        search_from = identifier_start
        if not separator:
            continue
        try:
            if str(UUID(attachment_id)) != attachment_id.lower():
                continue
        except ValueError:
            continue
        referenced_dirs.add(attachments / attachment_id)

    candidates: set[Path] = set()
    for attachment_dir in referenced_dirs:
        try:
            if not attachment_dir.is_dir():
                continue
            entries = attachment_dir.iterdir()
        except OSError:
            continue
        for entry in entries:
            if str(entry) not in objective:
                continue
            try:
                resolved = entry.resolve(strict=True)
                relative = resolved.relative_to(attachments)
            except (OSError, ValueError):
                continue
            if len(relative.parts) == 2 and resolved.is_file():
                candidates.add(resolved)

    if len(candidates) != 1:
        return None
    return candidates.pop()


def accounting_context(goal: dict[str, Any], tool_response: dict[str, Any]) -> str:
    """Render the structured completion fields that the final handoff must retain."""

    fields = [f"`goal.tokensUsed={goal.get('tokensUsed')!r}`"]
    if "tokenBudget" in goal:
        fields.append(f"`goal.tokenBudget={goal.get('tokenBudget')!r}`")
    else:
        fields.append("`goal.tokenBudget` is absent")
    fields.append(f"`goal.timeUsedSeconds={goal.get('timeUsedSeconds')!r}`")
    report = tool_response.get("completionBudgetReport")
    if isinstance(report, str) and report:
        fields.append(f"completion requirement: {report}")
    return "; ".join(fields)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        # A review hook must never interfere with successful goal completion.
        return 0

    if not isinstance(payload, dict):
        return 0

    tool_input = object_value(payload.get("tool_input"))
    if tool_input.get("status") != "complete":
        return 0

    tool_response = object_value(payload.get("tool_response"))
    goal = object_value(tool_response.get("goal"))
    response_status = goal.get("status")
    if response_status != "complete":
        return 0

    transcript_path = payload.get("transcript_path")
    session_id = payload.get("session_id")
    if not isinstance(transcript_path, str) or not transcript_path.strip():
        return 0
    if not isinstance(session_id, str) or not session_id.strip():
        session_id = "unknown"

    skill_path = Path(__file__).resolve().parent.parent / "SKILL.md"
    codex_home = Path(__file__).resolve().parents[3]
    extractor_path = (
        Path(__file__).resolve().parents[2]
        / "skill-researcher"
        / "scripts"
        / "extract_session_evidence.py"
    )
    goal_id = (
        goal.get("goalId") or goal.get("goal_id") or goal.get("threadId") or session_id
    )
    goal_file = referenced_goal_file(goal, codex_home)

    if goal_file is None:
        additional_context = (
            'A successful `update_goal(status="complete")` call just marked the active '
            "goal achieved, but its structured objective did not expose an exact managed "
            "harness goal file. Do not run the automatic post-goal skill review in this "
            "turn because the required write-ahead handoff cannot be made durable. Write "
            "the ordinary goal-completion final response now, preserving all result, "
            "verification, caveat, deferred-work, cleanup, and required goal-accounting "
            f"details. Structured completion accounting: {accounting_context(goal, tool_response)}"
        )
    else:
        begin_marker = f"<!-- codex-goal-completion-handoff:{goal_id}:begin -->"
        end_marker = f"<!-- codex-goal-completion-handoff:{goal_id}:end -->"
        additional_context = (
            'A successful `update_goal(status="complete")` call just marked the active '
            "goal achieved. Before reading `$auto-skill-enhancer`, running its extractor, "
            "or doing any post-goal review analysis, preserve the ordinary goal-completion "
            "handoff in the exact harness file dynamically exposed by the completed "
            f"`goal.objective`: `{goal_file}`. This write-ahead step is "
            "mandatory and comes first. Draft the complete final-ready goal result exactly "
            "as the user should receive it if this hook had never run. Include every material "
            "outcome, changed or installed surface, current state, verification command and "
            "result, failure or nonzero diagnostic distinction, caveat, deferred check, "
            "scope restriction honored, cleanup result, and required goal accounting; do "
            "not include the skill review. Structured completion accounting: "
            f"{accounting_context(goal, tool_response)}. Append that text exactly once, "
            "without changing earlier goal content, between these delimiter lines: "
            f"`{begin_marker}` and `{end_marker}`. If the delimited block already exists, "
            "reuse it. Re-read the saved block and confirm it before continuing. If the "
            "exact file cannot be written and re-read, do not start the review; immediately "
            "deliver the ordinary completion response from retained evidence. Only after "
            "the durable block is confirmed, run the post-goal skill review. Read "
            f"`$auto-skill-enhancer` completely at `{skill_path}` and follow its review-only "
            f"workflow. Use session `{session_id}`, goal `{goal_id}`, and transcript "
            f"`{transcript_path}`. Start with the researcher-owned bounded extractor at "
            f"`{extractor_path}` and pass `--exclude-skill auto-skill-enhancer`. Review only "
            "user-owned skills that the session proves were actually used. Do not edit any "
            "skill, hook, configuration, memory, repository, or transcript during this "
            "automatic pass. In the final response, first copy only the saved content "
            "between the delimiters verbatim, preserving its Markdown, whitespace, ordering, "
            "and nuance; exclude the delimiter lines themselves. Then add the post-goal "
            "skill review as a separate section. Do not summarize, rewrite, or merge the "
            "saved completion handoff. After any context compaction, re-read it from the "
            "harness goal file instead of reconstructing it. If this goal already has an "
            "auto-skill-enhancer review in the transcript, do not repeat it."
        )

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": additional_context,
        }
    }
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
