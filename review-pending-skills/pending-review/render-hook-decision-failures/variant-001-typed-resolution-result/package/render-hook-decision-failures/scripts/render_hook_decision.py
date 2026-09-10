#!/usr/bin/env python3
"""Render one typed decision result as a valid Codex PostToolUse envelope."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping


MODE = "typed-resolution-result"
EVENT_NAME = "PostToolUse"
MAX_DEPTH = 4
MAX_COLLECTION = 16
MAX_KEY_LENGTH = 64
MAX_STRING_LENGTH = 512
MAX_OUTPUT_BYTES = 8192
REQUIRED_FIELDS = {"status", "stage", "code", "condition", "expected", "received", "candidate_count"}


def normalize_home_text(value: str) -> str:
    """Normalize delimited home paths without rewriting sibling identities."""

    home = re.escape(str(Path.home().resolve(strict=False)))
    value = re.sub(rf"""(["'`]){home}\1""", r"\1~\1", value)
    return re.sub(r"""(?<![^\s"'`=:(\[{])""" + home + r"(?=/|$)", "~", value)


def safe_value(value: Any, *, depth: int = 0) -> Any:
    """Validate and normalize one domain-selected diagnostic value."""

    if depth > MAX_DEPTH:
        raise ValueError("diagnostic value exceeds the maximum nesting depth")
    if value is None or isinstance(value, (bool, int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("diagnostic numbers must be finite")
        return value
    if isinstance(value, str):
        if len(value) > MAX_STRING_LENGTH:
            raise ValueError("diagnostic strings must be bounded")
        if any(ord(character) < 32 and character not in "\t\n\r" for character in value):
            raise ValueError("diagnostic strings must not contain control bytes")
        return normalize_home_text(value)
    if isinstance(value, list):
        if len(value) > MAX_COLLECTION:
            raise ValueError("diagnostic arrays must be bounded")
        return [safe_value(item, depth=depth + 1) for item in value]
    if isinstance(value, Mapping):
        return _safe_mapping(value, depth)
    raise ValueError(f"unsupported diagnostic value type: {type(value).__name__}")


def _safe_mapping(value: Mapping[str, Any], depth: int) -> dict[str, Any]:
    """Validate object keys and refuse lossy presentation collisions."""

    if len(value) > MAX_COLLECTION:
        raise ValueError("diagnostic objects must be bounded")
    normalized: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key or len(key) > MAX_KEY_LENGTH:
            raise ValueError("diagnostic object keys must be short nonempty strings")
        key = safe_value(key)
        if key in normalized:
            raise ValueError("path normalization would collapse diagnostic keys")
        normalized[key] = safe_value(item, depth=depth + 1)
    return normalized


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
    if REQUIRED_FIELDS - value.keys() or value.keys() - (REQUIRED_FIELDS | {"artifact", "approach"}):
        raise ValueError("decision fields must match the declared schema")
    status = value.get("status")
    if not isinstance(status, str) or status not in {"success", "failure"}:
        raise ValueError("status must equal success or failure")
    candidate_count = value.get("candidate_count")
    if (
        not isinstance(candidate_count, (int, float))
        or isinstance(candidate_count, bool)
        or (isinstance(candidate_count, float) and not math.isfinite(candidate_count))
        or candidate_count < 0
        or int(candidate_count) != candidate_count
    ):
        raise ValueError("candidate_count must be a nonnegative integer")
    artifact = value.get("artifact")
    if artifact is not None:
        artifact = nonempty_text(value, "artifact")
    normalized = {
        "status": status,
        "stage": nonempty_text(value, "stage"),
        "code": nonempty_text(value, "code"),
        "condition": nonempty_text(value, "condition"),
        "expected": safe_value(value["expected"]),
        "received": safe_value(value["received"]),
        "candidate_count": int(candidate_count),
        "artifact": artifact,
    }
    if "approach" in value:
        normalized["approach"] = nonempty_text(value, "approach")
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


def serialize(output: Mapping[str, Any]) -> str:
    """Measure and emit the same JSON bytes, including the final newline."""

    return json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"


def bounded_envelope(context: str, status: str) -> dict[str, Any]:
    """Explicitly omit the original context when the whole response is too large."""

    output = envelope(context)
    size = len(serialize(output).encode("utf-8"))
    if size <= MAX_OUTPUT_BYTES:
        return output
    outcome = "succeeded" if status == "success" else "failed"
    return envelope(
        f"Hook decision {outcome}. Original diagnostic context omitted in full. "
        "Checked condition, expected, received, stage, code, and candidate count are unavailable "
        "in this bounded presentation. Renderer code: output-budget-exceeded. "
        f"Omitted context bytes: {len(context.encode('utf-8'))}. "
        f"Original serialized response bytes: {size}. Output budget bytes: {MAX_OUTPUT_BYTES}."
    )


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
    return bounded_envelope(context, decision["status"])


def invalid_input_envelope() -> dict[str, Any]:
    """Render a safe diagnostic without exposing rejected input or exceptions."""

    return envelope(
        "Hook decision failed. Checked condition: the typed decision result is complete and safe. "
        "Expected: a success-or-failure result with nonempty stage, code, and condition, "
        "explicit expected and received observations, and a nonnegative candidate_count. "
        "Received: invalid typed decision result; its contents were omitted. "
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

    for field in REQUIRED_FIELDS:
        missing = dict(failure_result)
        del missing[field]
        try:
            validate_result(missing)
        except ValueError:
            assertions += 1
        else:
            raise AssertionError(f"missing {field} was accepted")
    for changes in ({"unknown": 0}, {"approach": 9}, {"approach": None}, {"status": []}, {"candidate_count": True}):
        try:
            validate_result({**failure_result, **changes})
        except ValueError:
            assertions += 1
        else:
            raise AssertionError("malformed decision was accepted")
    for observation in ("", None, False, 0, [], {}):
        result = {**failure_result, "received": observation, "candidate_count": 1.0}
        del result["artifact"]
        assert validate_result(result)["received"] == observation
        assertions += 1
    home = str(Path.home().resolve(strict=False))
    values = {home: [home + "/goal", home + "-neighbor/goal", "prefix" + home + "/goal"]}
    assert safe_value(values) == {"~": ["~/goal", home + "-neighbor/goal", "prefix" + home + "/goal"]}
    assertions += 1
    wide: Any = "x" * 128
    for _ in range(3):
        wide = [wide] * 8
    bounded = render({**failure_result, "received": wide})
    assert len(serialize(bounded).encode("utf-8")) <= MAX_OUTPUT_BYTES
    assert "output-budget-exceeded" in bounded["hookSpecificOutput"]["additionalContext"]
    assert "Omitted context bytes:" in bounded["hookSpecificOutput"]["additionalContext"]
    assertions += 3
    deep = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--result-json", "[" * 1200 + "0" + "]" * 1200],
        capture_output=True, text=True, check=False,
    )
    assert deep.returncode == 0 and deep.stderr == ""
    assert "invalid-decision-result" in json.loads(deep.stdout)["hookSpecificOutput"]["additionalContext"]
    assertions += 2

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
    except (TypeError, ValueError, RecursionError, OverflowError):
        output = invalid_input_envelope()
    sys.stdout.write(serialize(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
