#!/usr/bin/env python3
"""Inject the durable goal-completion handoff after a successful completion."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping

from goal_artifact_resolution import GoalArtifactResolution, resolve_artifact


EVENT_NAME = "PostToolUse"
MARKER_COMPONENT_RE = re.compile(r"[^A-Za-z0-9._-]+")


def object_value(value: Any) -> dict[str, Any]:
    """Return an object supplied directly or as one JSON-encoded string."""

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


def normalize_home_text(value: str) -> str:
    """Render every expanded current-home occurrence as `~`."""

    home = str(Path.home().resolve(strict=False))
    return value.replace(home, "~")


def render_value(value: Any) -> str:
    """Render a resolver-selected safe diagnostic value deterministically."""

    return normalize_home_text(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    )


def accounting_context(goal: Mapping[str, Any], tool_response: Mapping[str, Any]) -> str:
    """Render the structured completion fields that the handoff must retain."""

    fields = [f"`goal.tokensUsed={goal.get('tokensUsed')!r}`"]
    if "tokenBudget" in goal:
        fields.append(f"`goal.tokenBudget={goal.get('tokenBudget')!r}`")
    else:
        fields.append("`goal.tokenBudget` is absent")
    fields.append(f"`goal.timeUsedSeconds={goal.get('timeUsedSeconds')!r}`")
    report = tool_response.get("completionBudgetReport")
    if isinstance(report, str) and report:
        fields.append(f"completion requirement: {normalize_home_text(report)}")
    return "; ".join(fields)


def completion_event(
    payload: Any,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """Return the completed goal and tool response for the exact trigger event."""

    if not isinstance(payload, dict):
        return None
    tool_input = object_value(payload.get("tool_input"))
    if tool_input.get("status") != "complete":
        return None
    tool_response = object_value(payload.get("tool_response"))
    goal = object_value(tool_response.get("goal"))
    if goal.get("status") != "complete":
        return None
    return goal, tool_response


def marker_identifier(goal: Mapping[str, Any], payload: Mapping[str, Any]) -> str:
    """Return one bounded, goal-specific delimiter component."""

    value = (
        goal.get("goalId")
        or goal.get("goal_id")
        or goal.get("threadId")
        or payload.get("session_id")
        or "unknown"
    )
    normalized = MARKER_COMPONENT_RE.sub("_", str(value).strip()).strip("_")
    return normalized[:128] or "unknown"


def envelope(context: str) -> dict[str, Any]:
    """Build the only hook output shape emitted by this adapter."""

    return {
        "hookSpecificOutput": {
            "hookEventName": EVENT_NAME,
            "additionalContext": context,
        }
    }


def failure_context(
    resolution: GoalArtifactResolution,
    goal: Mapping[str, Any],
    tool_response: Mapping[str, Any],
) -> str:
    """Render one actionable fail-open handoff diagnostic."""

    return (
        "The successful `update_goal(status=\"complete\")` result is preserved, but the "
        "durable goal-completion handoff prerequisite could not be resolved. "
        f"Checked condition: {resolution.condition}. "
        f"Expected: {render_value(resolution.expected)}. "
        f"Received: {render_value(resolution.received)}. "
        f"Stage: {resolution.stage}. Code: {resolution.code}. "
        f"Candidate count: {resolution.candidate_count}. "
        "Deliver the ordinary goal-completion response now, preserving all material "
        "outcome, verification, caveat, deferred-work, cleanup, and required accounting "
        f"details. Structured completion accounting: {accounting_context(goal, tool_response)}. "
        "Do not begin downstream post-completion work because its confirmed durable "
        "handoff prerequisite is unavailable."
    )


def success_context(
    resolution: GoalArtifactResolution,
    goal: Mapping[str, Any],
    tool_response: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> str:
    """Render the model-owned write-ahead handoff instructions."""

    goal_id = marker_identifier(goal, payload)
    begin_marker = f"<!-- codex-goal-completion-handoff:{goal_id}:begin -->"
    end_marker = f"<!-- codex-goal-completion-handoff:{goal_id}:end -->"
    return (
        "A successful `update_goal(status=\"complete\")` call just marked the active "
        "goal achieved. Before any downstream post-completion work, preserve the ordinary "
        f"goal-completion handoff in the exact managed harness file: `{resolution.artifact}`. "
        "Draft the complete final-ready result exactly as the user should receive it if no "
        "post-completion work ran. Include every material outcome, changed or installed "
        "surface, current state, verification command and result, failure or nonzero "
        "diagnostic distinction, caveat, deferred check, scope restriction honored, cleanup "
        "result, and required goal accounting. Structured completion accounting: "
        f"{accounting_context(goal, tool_response)}. Append that text exactly once, without "
        "changing earlier goal content, between these delimiter lines: "
        f"`{begin_marker}` and `{end_marker}`. If the delimited block already exists, reuse "
        "it. Re-read the saved block and confirm its exact content before continuing. "
        "Preserve that block verbatim as the ordinary completion portion of the final "
        "response. If the exact file cannot be written and re-read, immediately deliver the "
        "ordinary completion response from retained evidence and do not begin downstream "
        "post-completion work. The hook itself has not written the artifact."
    )


def build_output(payload: Any) -> dict[str, Any] | None:
    """Return one handoff context for a successful completion, otherwise no output."""

    event = completion_event(payload)
    if event is None or not isinstance(payload, dict):
        return None
    goal, tool_response = event
    resolution = resolve_artifact(goal.get("objective"))
    if resolution.status == "failure":
        return envelope(failure_context(resolution, goal, tool_response))
    return envelope(success_context(resolution, goal, tool_response, payload))


def main() -> int:
    """Read one hook event, fail open, keep stderr empty, and never mutate state."""

    try:
        payload = json.load(sys.stdin)
        output = build_output(payload)
    except (Exception, KeyboardInterrupt):
        return 0
    if output is not None:
        print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
