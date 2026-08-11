#!/usr/bin/env python3
"""Discover repository edit candidates without deciding authority or regression status."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from damage_common import AssessmentInputError, atomic_write_text, canonical_json, display_path, load_json


PATCH_FILE = re.compile(r"^\*\*\* (Add|Update|Delete) File: (.+)$")
WRITE_COMMAND = re.compile(
    r"(?:^|[;&|]\s*)(?:git\s+(?:add|rm|mv)|cargo\s+fmt|just\s+(?:fmt|gen-md)|"
    r"sed\s+-i|perl\s+-i|python\S*\s+.*(?:write_text|write_bytes|open\()|"
    r"mv\s+|cp\s+|rm\s+|install\s+|touch\s+|truncate\s+)",
    re.MULTILINE,
)


def parse_args() -> argparse.Namespace:
    """Parse the tool index, selected repository, and output path."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool-index", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def decode_tool_input(value: Any) -> Any:
    """Decode one JSON-encoded tool input layer when applicable."""
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped.startswith(("{", "[")):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def normalize_patch_input(value: Any) -> str | None:
    """Extract direct or JavaScript-wrapped `apply_patch` text."""
    decoded = decode_tool_input(value)
    if isinstance(decoded, str):
        if decoded.startswith("*** Begin Patch"):
            return decoded
        match = re.search(r"(?:const|let)\s+patch\s*=\s*(\"(?:\\.|[^\"\\])*\")\s*;", decoded, re.DOTALL)
        if match is None:
            return None
        try:
            patch = json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
        return patch if isinstance(patch, str) else None
    if isinstance(decoded, dict):
        for key in ("patch", "input"):
            candidate = decoded.get(key)
            if isinstance(candidate, str) and candidate.startswith("*** Begin Patch"):
                return candidate
    return None


def output_text(events: list[dict[str, Any]]) -> str:
    """Join complete correlated output values for conservative classification."""
    parts: list[str] = []
    for event in events:
        value = event.get("output")
        if value is None:
            value = event.get("payload_excerpt")
        parts.append(value if isinstance(value, str) else json.dumps(value, sort_keys=True))
    return "\n".join(parts)


def reported_success(events: list[dict[str, Any]]) -> bool | None:
    """Return conservative success, failure, or unknown from correlated outputs."""
    if not events:
        return None
    text = output_text(events).lower()
    failure_markers = (
        '"iserror":true',
        '"is_error":true',
        "traceback",
        "error:",
        "exit code: 1",
        '"exit_code":1',
        "patch failed",
    )
    return not any(marker in text for marker in failure_markers)


def within_repository(candidate: Path, repository: Path) -> bool:
    """Return whether a lexical target resolves beneath the selected repository."""
    try:
        candidate.resolve(strict=False).relative_to(repository)
    except (OSError, ValueError):
        return False
    return True


def patch_operations(patch: str, repository: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Return in-repository operations and rejected target declarations."""
    operations: list[dict[str, str]] = []
    rejected: list[str] = []
    for line in patch.splitlines():
        match = PATCH_FILE.match(line)
        if match is None:
            continue
        operation, target = match.groups()
        target_path = Path(target)
        resolved = target_path if target_path.is_absolute() else repository / target_path
        if not within_repository(resolved, repository):
            rejected.append(target)
            continue
        operations.append(
            {
                "operation": operation.lower(),
                "target": str(resolved.resolve(strict=False).relative_to(repository)),
            }
        )
    return operations, rejected


def session_documents(index: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize current multi-session and historical single-session indexes."""
    sessions = index.get("sessions")
    if isinstance(sessions, list):
        return [session for session in sessions if isinstance(session, dict)]
    if isinstance(index.get("correlations"), list):
        return [{"session_index": 0, "rollout_id": index.get("rollout_id"), "correlations": index["correlations"]}]
    raise AssessmentInputError("tool index: expected `sessions` or `correlations`")


def main() -> int:
    """Write edit candidates and unsupported mutation-shaped calls for review."""
    arguments = parse_args()
    repository = arguments.repository.expanduser().resolve(strict=True)
    try:
        index = load_json(arguments.tool_index.expanduser())
        if not isinstance(index, dict):
            raise AssessmentInputError("tool index: expected object")
        candidates: list[dict[str, Any]] = []
        unsupported: list[dict[str, Any]] = []
        for session in session_documents(index):
            correlations = session.get("correlations")
            if not isinstance(correlations, list):
                raise AssessmentInputError("tool index session: expected `correlations` array")
            for correlation in correlations:
                if not isinstance(correlation, dict):
                    continue
                calls = correlation.get("call_events")
                outputs = correlation.get("output_events")
                if not isinstance(calls, list) or not isinstance(outputs, list) or len(calls) != 1:
                    continue
                call = calls[0]
                if not isinstance(call, dict):
                    continue
                decoded = decode_tool_input(call.get("input"))
                patch = normalize_patch_input(decoded)
                common = {
                    "session_index": session.get("session_index", 0),
                    "rollout_id": session.get("rollout_id"),
                    "call_id": correlation.get("call_id"),
                    "ordinal": call.get("ordinal"),
                    "timestamp": call.get("timestamp"),
                    "tool": call.get("name"),
                    "reported_success": reported_success([event for event in outputs if isinstance(event, dict)]),
                    "output_ordinals": [event.get("ordinal") for event in outputs if isinstance(event, dict)],
                    "output_excerpt": output_text([event for event in outputs if isinstance(event, dict)])[:2_000],
                }
                if call.get("name") == "apply_patch" or patch is not None:
                    if patch is None:
                        unsupported.append({**common, "reason": "apply_patch input could not be decoded"})
                        continue
                    operations, rejected = patch_operations(patch, repository)
                    if operations:
                        candidates.append(
                            {**common, "kind": "structured_patch", "operations": operations, "rejected_targets": rejected, "patch": patch}
                        )
                    elif rejected:
                        unsupported.append({**common, "reason": "patch targets fall outside selected repository", "targets": rejected})
                    continue
                if call.get("name") != "exec_command" or not isinstance(decoded, dict):
                    continue
                workdir = decoded.get("workdir")
                command = decoded.get("cmd")
                if not isinstance(workdir, str) or not isinstance(command, str):
                    continue
                under_repository = within_repository(Path(workdir).expanduser(), repository)
                if under_repository and WRITE_COMMAND.search(command):
                    candidates.append(
                        {**common, "kind": "shell_mutation_candidate", "workdir": display_path(Path(workdir)), "command": command}
                    )
                elif under_repository and any(token in command for token in (">", "tee ", "xargs", "-exec")):
                    unsupported.append({**common, "reason": "unclassified repository command may mutate", "command": command})

        ordering = lambda item: (int(item.get("session_index", 0)), int(item.get("ordinal") or -1), str(item.get("call_id")))
        result = {
            "schema_version": 1,
            "repository": display_path(repository),
            "tool_index": display_path(arguments.tool_index),
            "candidates": sorted(candidates, key=ordering),
            "unsupported_mutation_shaped_calls": sorted(unsupported, key=ordering),
        }
        atomic_write_text(arguments.output.expanduser(), canonical_json(result))
    except (AssessmentInputError, OSError) as error:
        raise SystemExit(str(error)) from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
