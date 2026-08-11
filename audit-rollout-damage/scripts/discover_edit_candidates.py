#!/usr/bin/env python3
"""Discover repository edit candidates without deciding authority or regression status."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from damage_common import (
    AssessmentInputError,
    atomic_write_text,
    canonical_json,
    display_path,
    load_json,
    normalize_home_text,
    normalize_home_value,
)


PATCH_FILE = re.compile(r"^\*\*\* (Add|Update|Delete) File: (.+)$")
WRITE_COMMAND = re.compile(
    r"(?:^|[;&|]\s*)(?:git\s+(?:add|rm|mv)|cargo\s+fmt|just\s+(?:fmt|gen-md)|"
    r"sed\s+-i|perl\s+-i|python\S*\s+.*(?:write_text|write_bytes|open\()|"
    r"mv\s+|cp\s+|rm\s+|install\s+|touch\s+|truncate\s+)",
    re.MULTILINE,
)
NESTED_EXEC_COMMAND = re.compile(r"\btools\.exec_command\s*\(")
EMBEDDED_WRITE_COMMAND = re.compile(
    r"\b(?:git\s+(?:add|rm|mv)|cargo\s+fmt|just\s+(?:fmt|gen-md)|"
    r"sed\s+-i|perl\s+-i|mv|cp|rm|install|touch|truncate)\b|"
    r"\bpython\S*\b[^\n]*(?:write_text|write_bytes|open\()",
    re.MULTILINE,
)
SUCCESS_STATUSES = {"ok", "success", "succeeded"}
FAILURE_STATUSES = {"cancelled", "error", "failed", "failure", "timed_out", "timeout"}
TRANSPORT_COMPLETION_STATUSES = {"completed"}
RESULT_CONTAINER_KEYS = {
    "content",
    "data",
    "output",
    "result",
    "structuredContent",
    "structured_content",
}


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
    """Join complete correlated output values for review evidence."""
    parts: list[str] = []
    for event in events:
        value = event.get("output")
        if value is None:
            value = event.get("payload_excerpt")
        normalized = normalize_home_value(value)
        parts.append(
            normalized
            if isinstance(normalized, str)
            else json.dumps(normalized, sort_keys=True, ensure_ascii=False)
        )
    return "\n".join(parts)


def result_signals(value: Any) -> tuple[list[bool], list[bool]]:
    """Collect decisive result signals separately from transport completion."""
    decoded = decode_tool_input(value)
    if decoded is not value:
        return result_signals(decoded)
    if isinstance(decoded, list):
        decisive: list[bool] = []
        transport: list[bool] = []
        for item in decoded:
            item_decisive, item_transport = result_signals(item)
            decisive.extend(item_decisive)
            transport.extend(item_transport)
        return decisive, transport
    if not isinstance(decoded, dict):
        return [], []

    decisive: list[bool] = []
    transport: list[bool] = []
    for key in ("isError", "is_error"):
        marker = decoded.get(key)
        if isinstance(marker, bool):
            decisive.append(not marker)
    for key in ("success", "ok"):
        marker = decoded.get(key)
        if isinstance(marker, bool):
            decisive.append(marker)
    for key in ("exit_code", "exitCode", "return_code", "returncode"):
        status = decoded.get(key)
        if isinstance(status, int) and not isinstance(status, bool):
            decisive.append(status == 0)
    status = decoded.get("status")
    if isinstance(status, str):
        normalized_status = status.strip().lower().replace("-", "_").replace(" ", "_")
        if normalized_status in SUCCESS_STATUSES:
            decisive.append(True)
        elif normalized_status in FAILURE_STATUSES:
            decisive.append(False)
        elif normalized_status in TRANSPORT_COMPLETION_STATUSES:
            transport.append(True)

    for key in RESULT_CONTAINER_KEYS:
        if key in decoded:
            nested_decisive, nested_transport = result_signals(decoded[key])
            decisive.extend(nested_decisive)
            transport.extend(nested_transport)
    return decisive, transport


def reported_success(events: list[dict[str, Any]]) -> bool | None:
    """Return success or failure only when structured result semantics agree."""
    if not events:
        return None
    decisive: list[bool] = []
    transport: list[bool] = []
    for event in events:
        event_decisive, event_transport = result_signals(event)
        decisive.extend(event_decisive)
        transport.extend(event_transport)
    signals = decisive or transport
    if not signals or len(set(signals)) != 1:
        return None
    return signals[0]


def wrapper_source(value: Any) -> str | None:
    """Return JavaScript source from a raw or object-wrapped `exec` input."""
    decoded = decode_tool_input(value)
    if isinstance(decoded, str):
        return decoded
    if isinstance(decoded, dict):
        for key in ("code", "source", "input"):
            source = decoded.get(key)
            if isinstance(source, str):
                return source
    return None


def nested_exec_command_inputs(source: str) -> tuple[list[dict[str, Any]], int]:
    """Decode strict JSON object arguments from nested `tools.exec_command` calls."""
    decoder = json.JSONDecoder()
    invocations: list[dict[str, Any]] = []
    failures = 0
    for match in NESTED_EXEC_COMMAND.finditer(source):
        position = match.end()
        while position < len(source) and source[position].isspace():
            position += 1
        try:
            value, end = decoder.raw_decode(source, position)
        except json.JSONDecodeError:
            failures += 1
            continue
        while end < len(source) and source[end].isspace():
            end += 1
        if not isinstance(value, dict) or end >= len(source) or source[end] != ")":
            failures += 1
            continue
        invocations.append(value)
    return invocations, failures


def mutation_shaped(command: str) -> bool:
    """Return whether visible command text has a repository-mutation shape."""
    return bool(WRITE_COMMAND.search(command) or EMBEDDED_WRITE_COMMAND.search(command)) or any(
        token in command for token in (">", "tee ", "xargs", "-exec")
    )


def classify_exec_command(
    value: dict[str, Any],
    common: dict[str, Any],
    repository: Path,
    candidates: list[dict[str, Any]],
    unsupported: list[dict[str, Any]],
    *,
    nested_index: int | None = None,
) -> None:
    """Classify one direct or exactly decoded nested `exec_command` input."""
    workdir = value.get("workdir")
    command = value.get("cmd")
    nested = (
        {"nested_tool": "exec_command", "nested_index": nested_index}
        if nested_index is not None
        else {}
    )
    if not isinstance(command, str):
        return
    command = normalize_home_text(command)
    if not isinstance(workdir, str):
        if mutation_shaped(command):
            unsupported.append(
                {
                    **common,
                    **nested,
                    "reason": "mutation-shaped exec_command lacks an explicit workdir",
                    "command": command,
                }
            )
        return
    under_repository = within_repository(Path(workdir).expanduser(), repository)
    if under_repository and WRITE_COMMAND.search(command):
        candidates.append(
            {
                **common,
                **nested,
                "kind": "shell_mutation_candidate",
                "workdir": display_path(Path(workdir)),
                "command": command,
            }
        )
    elif under_repository and mutation_shaped(command):
        unsupported.append(
            {
                **common,
                **nested,
                "reason": "unclassified repository command may mutate",
                "command": command,
            }
        )


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
                output_events = [event for event in outputs if isinstance(event, dict)]
                common = {
                    "session_index": session.get("session_index", 0),
                    "rollout_id": session.get("rollout_id"),
                    "call_id": correlation.get("call_id"),
                    "ordinal": call.get("ordinal"),
                    "timestamp": call.get("timestamp"),
                    "tool": call.get("name"),
                    "reported_success": reported_success(output_events),
                    "output_ordinals": [event.get("ordinal") for event in outputs if isinstance(event, dict)],
                    "output_excerpt": output_text(output_events)[:2_000],
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
                    if call.get("name") == "apply_patch":
                        continue
                if call.get("name") == "exec_command" and isinstance(decoded, dict):
                    classify_exec_command(decoded, common, repository, candidates, unsupported)
                    continue
                if call.get("name") != "exec":
                    continue
                source = wrapper_source(decoded)
                if source is None:
                    continue
                nested_inputs, parse_failures = nested_exec_command_inputs(source)
                for nested_index, nested_input in enumerate(nested_inputs):
                    classify_exec_command(
                        nested_input,
                        common,
                        repository,
                        candidates,
                        unsupported,
                        nested_index=nested_index,
                    )
                if parse_failures and mutation_shaped(source):
                    unsupported.append(
                        {
                            **common,
                            "reason": "mutation-shaped exec wrapper contains unparsed tools.exec_command input",
                            "unparsed_nested_calls": parse_failures,
                            "wrapper_excerpt": normalize_home_text(source)[:2_000],
                        }
                    )

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
