#!/usr/bin/env python3
"""Render one typed decision result as a valid Codex PostToolUse envelope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping


MODE = "typed-resolution-result"
EVENT_NAME = "PostToolUse"
MAX_DEPTH = 4
MAX_COLLECTION = 16
MAX_KEY_LENGTH = 64
MAX_STRING_LENGTH = 512


def normalize_home_text(value: str) -> str:
    """Normalize every expanded current-home occurrence for rendering."""

    home = str(Path.home().resolve(strict=False))
    return value.replace(home, "~")


def safe_value(value: Any, *, depth: int = 0) -> Any:
    """Validate and normalize one domain-selected diagnostic value."""

    if depth > MAX_DEPTH:
        raise ValueError("diagnostic value exceeds the maximum nesting depth")
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        if not value or len(value) > MAX_STRING_LENGTH:
            raise ValueError("diagnostic strings must be nonempty and bounded")
        if any(ord(character) < 32 and character not in "\t\n\r" for character in value):
            raise ValueError("diagnostic strings must not contain control bytes")
        return normalize_home_text(value)
    if isinstance(value, list):
        if len(value) > MAX_COLLECTION:
            raise ValueError("diagnostic arrays must be bounded")
        return [safe_value(item, depth=depth + 1) for item in value]
    if isinstance(value, Mapping):
        if len(value) > MAX_COLLECTION:
            raise ValueError("diagnostic objects must be bounded")
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key or len(key) > MAX_KEY_LENGTH:
                raise ValueError("diagnostic object keys must be short nonempty strings")
            normalized[key] = safe_value(item, depth=depth + 1)
        return normalized
    raise ValueError(f"unsupported diagnostic value type: {type(value).__name__}")


def nonempty_text(result: Mapping[str, Any], name: str) -> str:
    """Read one required nonempty diagnostic field."""

    value = result.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty text")
    return safe_value(value)


def validate_result(value: Any) -> dict[str, Any]:
    """Validate both success and failure forms of a typed decision result."""

    if not isinstance(value, Mapping):
        raise ValueError("decision result must be an object")
    status = value.get("status")
    if status not in {"success", "failure"}:
        raise ValueError("status must equal success or failure")
    candidate_count = value.get("candidate_count")
    if (
        not isinstance(candidate_count, int)
        or isinstance(candidate_count, bool)
        or candidate_count < 0
    ):
        raise ValueError("candidate_count must be a nonnegative integer")
    artifact = value.get("artifact")
    if artifact is not None:
        artifact = safe_value(artifact)
        if not isinstance(artifact, str):
            raise ValueError("artifact must be text or null")
    normalized = {
        "status": status,
        "stage": nonempty_text(value, "stage"),
        "code": nonempty_text(value, "code"),
        "condition": nonempty_text(value, "condition"),
        "expected": safe_value(value.get("expected")),
        "received": safe_value(value.get("received")),
        "candidate_count": candidate_count,
        "artifact": artifact,
    }
    approach = value.get("approach")
    if approach is not None:
        normalized["approach"] = safe_value(approach)
    return normalized


def render_value(value: Any) -> str:
    """Render a normalized diagnostic value compactly and deterministically."""

    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def envelope(context: str) -> dict[str, Any]:
    """Build the only valid hook output shape owned by this renderer."""

    if not context:
        raise ValueError("additionalContext must be nonempty")
    return {
        "hookSpecificOutput": {
            "hookEventName": EVENT_NAME,
            "additionalContext": context,
        }
    }


def render(result: Any) -> dict[str, Any]:
    """Render one typed result without custom top-level fields."""

    decision = validate_result(result)
    if decision["status"] == "failure":
        context = (
            "Hook decision failed. "
            f"Checked condition: {decision['condition']}. "
            f"Expected: {render_value(decision['expected'])}. "
            f"Received: {render_value(decision['received'])}. "
            f"Stage: {decision['stage']}. "
            f"Code: {decision['code']}. "
            f"Candidate count: {decision['candidate_count']}."
        )
    else:
        context = (
            "Hook decision succeeded. "
            f"Checked condition: {decision['condition']}. "
            f"Expected: {render_value(decision['expected'])}. "
            f"Received: {render_value(decision['received'])}. "
            f"Stage: {decision['stage']}. "
            f"Code: {decision['code']}. "
            f"Candidate count: {decision['candidate_count']}."
        )
    return envelope(context)


def invalid_input_envelope() -> dict[str, Any]:
    """Render a safe diagnostic without exposing rejected input or exceptions."""

    return envelope(
        "Hook decision failed. Checked condition: the typed decision result is complete and safe. "
        "Expected: a success-or-failure result with nonempty stage, code, condition, expected, "
        "received, and candidate_count fields. Received: invalid typed decision result. "
        "Stage: render-hook-decision. Code: invalid-decision-result. Candidate count: 0."
    )


def self_test() -> dict[str, Any]:
    """Exercise both result forms, safe rendering, and direct process channels."""

    assertions = 0
    failure_result = {
        "status": "failure",
        "stage": "resolve-managed-goal-artifact",
        "code": "attachments-root-mismatch",
        "condition": "the candidate remains beneath the trusted attachments root",
        "expected": {"root": f"{Path.home()}/.codex/attachments"},
        "received": {"root": f"{Path.home()}/attachments"},
        "candidate_count": 1,
        "artifact": None,
    }
    failure_output = render(failure_result)
    assert set(failure_output) == {"hookSpecificOutput"}
    hook_output = failure_output["hookSpecificOutput"]
    assert set(hook_output) == {"hookEventName", "additionalContext"}
    assert hook_output["hookEventName"] == EVENT_NAME
    assert "Checked condition:" in hook_output["additionalContext"]
    assert "Expected:" in hook_output["additionalContext"]
    assert "Received:" in hook_output["additionalContext"]
    assert "Stage: resolve-managed-goal-artifact" in hook_output["additionalContext"]
    assert "Code: attachments-root-mismatch" in hook_output["additionalContext"]
    assert str(Path.home()) not in hook_output["additionalContext"]
    assertions += 9

    success_result = {
        "status": "success",
        "stage": "resolve-managed-goal-artifact",
        "code": "resolved-exact-artifact",
        "condition": "one exact regular artifact is named",
        "expected": {"candidate_count": 1},
        "received": {"candidate_count": 1},
        "candidate_count": 1,
        "artifact": f"{Path.home()}/.codex/attachments/id/goal",
        "approach": "environment-root",
    }
    success_output = render(success_result)
    success_context = success_output["hookSpecificOutput"]["additionalContext"]
    assert "succeeded" in success_context
    assert "failed" not in success_context
    assert "failure" not in success_context
    assertions += 3

    for field in ("stage", "code", "condition"):
        invalid = dict(failure_result)
        invalid[field] = ""
        try:
            render(invalid)
        except ValueError:
            assertions += 1
        else:
            raise AssertionError(f"empty {field} was accepted")

    invalid_count = dict(failure_result)
    invalid_count["candidate_count"] = -1
    try:
        render(invalid_count)
    except ValueError:
        assertions += 1
    else:
        raise AssertionError("negative candidate_count was accepted")

    unsafe = dict(failure_result)
    unsafe["received"] = "x" * (MAX_STRING_LENGTH + 1)
    try:
        render(unsafe)
    except ValueError:
        assertions += 1
    else:
        raise AssertionError("unbounded received value was accepted")

    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--result-json",
            json.dumps(failure_result),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stderr == ""
    assert json.loads(completed.stdout) == failure_output
    assertions += 3

    invalid_process = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--result-json", "[]"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    assert invalid_process.returncode == 0
    assert invalid_process.stderr == ""
    invalid_output = json.loads(invalid_process.stdout)
    assert set(invalid_output) == {"hookSpecificOutput"}
    assert "invalid-decision-result" in invalid_output["hookSpecificOutput"]["additionalContext"]
    assertions += 4

    return {"status": "passed", "assertions": assertions, "mode": MODE}


def parse_args() -> argparse.Namespace:
    """Parse one typed result or packaged self-test request."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-json")
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if not arguments.self_test and arguments.result_json is None:
        parser.error("--result-json is required unless --self-test is used")
    return arguments


def main() -> int:
    """Write one JSON object to stdout, keep stderr empty, and fail open."""

    arguments = parse_args()
    if arguments.self_test:
        print(json.dumps(self_test(), indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    try:
        value = json.loads(arguments.result_json)
        output = render(value)
    except (json.JSONDecodeError, TypeError, ValueError):
        output = invalid_input_envelope()
    print(json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
