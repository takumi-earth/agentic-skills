#!/usr/bin/env python3
"""Render a typed hook decision failure without losing diagnostic fields."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


MODE = "typed-resolution-result"
HOME = str(Path.home().resolve())


def normalize(value: Any) -> Any:
    if isinstance(value, str):
        if value == HOME:
            return "~"
        return value.replace(f"{HOME}/", "~/")
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize(item) for key, item in value.items()}
    return value


def render(stage: str, code: str, condition: str, expected: Any, received: Any) -> dict[str, Any]:
    decision = normalize({
        "status": "failure",
        "stage": stage,
        "code": code,
        "condition": condition,
        "expected": expected,
        "received": received,
    })
    context = (
        f"Hook decision failed: stage={stage}; code={code}; condition={condition}; "
        f"expected={json.dumps(decision['expected'], sort_keys=True)}; "
        f"received={json.dumps(decision['received'], sort_keys=True)}."
    )
    return {"additionalContext": context, "decision": decision, "mode": MODE}


def self_test() -> dict[str, Any]:
    output = render(
        "resolve-goal-file",
        "attachments-root-mismatch",
        "derived attachments root equals configured root",
        "~/.codex/attachments",
        "~/attachments",
    )
    assert output["decision"]["expected"] == "~/.codex/attachments"
    assert output["decision"]["received"] == "~/attachments"
    assert "condition=derived attachments root equals configured root" in output["additionalContext"]
    assert json.loads(json.dumps(output))["mode"] == MODE
    return {"status": "passed", "assertions": 4, "mode": MODE}


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
    output = render(
        arguments.stage,
        arguments.code,
        arguments.condition,
        parse_json_value(arguments.expected),
        parse_json_value(arguments.received),
    )
    if arguments.hook_only:
        output = {"additionalContext": output["additionalContext"]}
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
