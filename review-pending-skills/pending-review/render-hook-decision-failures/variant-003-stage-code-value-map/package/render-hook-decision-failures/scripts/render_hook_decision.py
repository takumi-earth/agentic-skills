#!/usr/bin/env python3
"""Render a compact stable stage/code/value hook diagnostic."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


MODE = "stage-code-value-map"
HOME = str(Path.home().resolve())
MAX_DEPTH = 32
MAX_OUTPUT_BYTES = 8192


def normalize(value: Any, depth: int = 0) -> Any:
    if depth > MAX_DEPTH:
        raise ValueError("diagnostic value exceeds the nesting limit")
    if isinstance(value, str):
        home = re.escape(HOME)
        value = re.sub(rf"""(["'`]){home}\1""", r"\1~\1", value)
        return re.sub(r"""(?<![^\s"'`=:(\[{])""" + home + r"(?=/|$)", "~", value)
    if isinstance(value, list):
        return [normalize(item, depth + 1) for item in value]
    if isinstance(value, dict):
        return _normalize_mapping(value, depth)
    if value is None or isinstance(value, (bool, int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("diagnostic numbers must be finite")
        return value
    raise ValueError("diagnostic values must be JSON values")


def _normalize_mapping(value: dict[str, Any], depth: int) -> dict[str, Any]:
    """Preserve each object entry when displaying normalized path keys."""

    result = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("diagnostic keys must be strings")
        key = normalize(key)
        if key in result:
            raise ValueError("path normalization would collapse diagnostic keys")
        result[key] = normalize(item, depth + 1)
    return result


def render(stage: str, code: str, condition: str, expected: Any, received: Any) -> dict[str, Any]:
    if not all(isinstance(value, str) and value.strip() for value in (stage, code, condition)):
        raise ValueError("stage, code, and condition must be nonempty text")
    values = normalize({
        "stage": stage,
        "code": code,
        "condition": condition,
        "expected": expected,
        "received": received,
    })
    ordered = ["stage", "code", "condition", "expected", "received"]
    context = "; ".join(
        f"{key}={json.dumps(values[key], sort_keys=True)}" for key in ordered
    )
    return {"additionalContext": f"Hook decision failed: {context}.", "diagnostic": values, "mode": MODE}


def serialize(output: dict[str, Any]) -> str:
    return json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"


def output_shape(output: dict[str, Any], hook_only: bool) -> dict[str, Any]:
    if hook_only:
        return {"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": output["additionalContext"],
        }}
    return output


def bounded_output(output: dict[str, Any], hook_only: bool = False) -> dict[str, Any]:
    shaped = output_shape(output, hook_only)
    size = len(serialize(shaped).encode("utf-8"))
    if size <= MAX_OUTPUT_BYTES:
        return shaped
    omitted = len(output["additionalContext"].encode("utf-8"))
    diagnostic = render(
        "render-hook-decision", "output-budget-exceeded",
        f"original diagnostic omitted in full; omitted context bytes: {omitted}",
        {"maximum_serialized_bytes": MAX_OUTPUT_BYTES},
        {"original_serialized_bytes": size},
    )
    return output_shape(diagnostic, hook_only)


def invalid_input_output() -> dict[str, Any]:
    return render(
        "render-hook-decision", "invalid-decision-input",
        "identifying fields are nonempty text and values are supported JSON or literals",
        "valid identifying fields and values", "invalid input; contents omitted",
    )


def self_test() -> dict[str, Any]:
    output = render("resolve", "zero-candidates", "candidate count equals one", 1, 0)
    context = output["additionalContext"]
    assert context.index("stage=") < context.index("code=") < context.index("condition=")
    assert context.index("expected=") < context.index("received=")
    assert output["diagnostic"]["expected"] == 1
    assert output["diagnostic"]["received"] == 0
    assertions = 4
    sibling = HOME + "-neighbor/session"
    assert normalize({HOME: [HOME + "/session", sibling, "prefix" + HOME]}) == {"~": ["~/session", sibling, "prefix" + HOME]}
    assert render("resolve", "missing", "value exists", None, [0, False, {}])["diagnostic"]["received"] == [0, False, {}]
    assertions += 2
    command = [sys.executable, str(Path(__file__).resolve()), "--stage", "resolve", "--code", "mismatch", "--condition", "value matches", "--expected", "null"]
    cases = (
        (["--received", "[0,false,{}]", "--hook-only"], "mismatch"),
        (["--received", "0", "--stage", ""], "invalid-decision-input"),
        (["--received", "[" * 1200 + "0" + "]" * 1200], "invalid-decision-input"),
        (["--received", "x" * 65536], "output-budget-exceeded"),
        (["--received", "0", "--stage", "x" * 65536, "--hook-only"], "output-budget-exceeded"),
    )
    for arguments, code in cases:
        result = subprocess.run([*command, *arguments], capture_output=True, text=True, check=False)
        assert result.returncode == 0 and result.stderr == ""
        assert len(result.stdout.encode("utf-8")) <= MAX_OUTPUT_BYTES
        document = json.loads(result.stdout)
        if "--hook-only" in arguments:
            assert set(document) == {"hookSpecificOutput"}
            assert document["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
            context = document["hookSpecificOutput"]["additionalContext"]
            assertions += 2
        else:
            context = document["additionalContext"]
        assert code in context
        assertions += 3
    return {"status": "passed", "assertions": assertions, "mode": MODE}


def parse_json_value(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage")
    parser.add_argument("--code")
    parser.add_argument("--condition")
    parser.add_argument("--expected")
    parser.add_argument("--received")
    parser.add_argument("--hook-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if not arguments.self_test:
        for name in ("stage", "code", "condition", "expected", "received"):
            if getattr(arguments, name) is None:
                parser.error(f"--{name.replace('_', '-')} is required")
    return arguments


def main() -> int:
    arguments = parse_args()
    if arguments.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return 0
    try:
        output = render(arguments.stage, arguments.code, arguments.condition, parse_json_value(arguments.expected), parse_json_value(arguments.received))
        output = bounded_output(output, arguments.hook_only)
        serialized = serialize(output)
    except (TypeError, ValueError, RecursionError, OverflowError):
        serialized = serialize(output_shape(invalid_input_output(), arguments.hook_only))
    sys.stdout.write(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
