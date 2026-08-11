#!/usr/bin/env python3
"""Inject only the automatic post-completion skill-review workflow."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any, Callable, Mapping


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


def display_path(path: Path) -> str:
    """Render paths beneath the current home directory as `~/...`."""

    absolute = path.expanduser().absolute()
    home = Path.home().resolve(strict=False)
    try:
        relative = absolute.relative_to(home)
    except ValueError:
        return str(absolute)
    return "~" if relative == Path(".") else f"~/{relative.as_posix()}"


def normalize_home_text(value: str) -> str:
    """Normalize expanded current-home occurrences without treating text as a path."""

    return value.replace(str(Path.home().resolve(strict=False)), "~")


def lexical_package_root() -> Path:
    """Keep the invoked package projection lexical for sibling resources."""

    return Path(__file__).absolute().parent.parent


def shared_resolver_path() -> Path:
    """Locate the declared sibling package resource without inferring harness state."""

    package_root = lexical_package_root()
    return (
        package_root.parent
        / "maintain-living-goal"
        / "scripts"
        / "goal_artifact_resolution.py"
    )


def load_shared_resolver() -> Callable[..., Any] | None:
    """Load the sibling-owned pure resolver, failing closed for review activation."""

    source = shared_resolver_path()
    if not source.is_file():
        return None
    module_name = "_goal_artifact_resolution_" + hashlib.sha256(
        str(source).encode("utf-8")
    ).hexdigest()[:16]
    try:
        spec = importlib.util.spec_from_file_location(module_name, source)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    except (Exception, KeyboardInterrupt):
        sys.modules.pop(module_name, None)
        return None
    resolver = getattr(module, "resolve_artifact", None)
    return resolver if callable(resolver) else None


def completion_event(payload: Any) -> dict[str, Any] | None:
    """Return the completed goal for the exact automatic-review trigger event."""

    if not isinstance(payload, dict):
        return None
    tool_input = object_value(payload.get("tool_input"))
    if tool_input.get("status") != "complete":
        return None
    tool_response = object_value(payload.get("tool_response"))
    goal = object_value(tool_response.get("goal"))
    if goal.get("status") != "complete":
        return None
    return goal


def resolve_goal(goal: Mapping[str, Any]) -> Any | None:
    """Independently resolve this handler's immutable goal objective."""

    resolver = load_shared_resolver()
    if resolver is None:
        return None
    try:
        return resolver(goal.get("objective"))
    except (Exception, KeyboardInterrupt):
        return None


def marker_identifier(goal: Mapping[str, Any], payload: Mapping[str, Any]) -> str:
    """Return the same bounded, goal-specific delimiter component as the owner."""

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


def build_output(payload: Any) -> dict[str, Any] | None:
    """Return automatic-review context only when every external prerequisite exists."""

    goal = completion_event(payload)
    if goal is None or not isinstance(payload, dict):
        return None
    session_id = payload.get("session_id")
    transcript_path = payload.get("transcript_path")
    if not isinstance(session_id, str) or not session_id.strip():
        return None
    if not isinstance(transcript_path, str) or not transcript_path.strip():
        return None

    resolution = resolve_goal(goal)
    if (
        resolution is None
        or getattr(resolution, "status", None) != "success"
        or not isinstance(getattr(resolution, "artifact", None), str)
    ):
        return None

    package_root = lexical_package_root()
    repository_root = package_root.parent
    skill_path = package_root / "SKILL.md"
    extractor_path = (
        repository_root
        / "skill-researcher"
        / "scripts"
        / "extract_session_evidence.py"
    )
    goal_id = marker_identifier(goal, payload)
    begin_marker = f"<!-- codex-goal-completion-handoff:{goal_id}:begin -->"
    end_marker = f"<!-- codex-goal-completion-handoff:{goal_id}:end -->"
    context = (
        "The automatic post-completion skill review is eligible to run only after the "
        "separate lifecycle handoff has become durable. Confirm that the earlier ordered "
        "completion-handoff context was received and that the exact block between "
        f"`{begin_marker}` and `{end_marker}` has been written to and re-read from "
        f"`{resolution.artifact}`. Do not create, repair, or reconstruct that block in this "
        "review handler. If the ordered handoff context is absent, the exact block cannot "
        "be confirmed, or the handoff otherwise failed, skip the automatic review and "
        "deliver the ordinary completion result. Only after confirmation, read "
        f"`$auto-skill-enhancer` completely at `{display_path(skill_path)}` and follow its "
        "automatic, read-only evidence-analysis workflow. Use session "
        f"`{session_id}`, goal `{goal_id}`, and transcript "
        f"`{normalize_home_text(transcript_path)}`. Start with "
        f"the bounded extractor at `{display_path(extractor_path)}` and pass "
        "`--exclude-skill auto-skill-enhancer`. Preserve its session, transcript, bounded "
        "extraction, complete-candidate inventory, creator handoff, and no-repeat "
        "requirements. Do not edit a skill, hook, configuration, memory, repository, goal "
        "artifact, or transcript as part of the enhancement analysis itself. In the final "
        "response, first copy only the confirmed saved block verbatim, preserving its "
        "Markdown, whitespace, ordering, and nuance; then add the automatic skill-"
        "maintenance result as a separate section. If this goal already has an automatic "
        "skill review in the transcript, do not repeat it."
    )
    return envelope(context)


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
