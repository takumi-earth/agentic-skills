#!/usr/bin/env python3
"""Render a compact stable stage/code/value hook diagnostic."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


MODE = "stage-code-value-map"
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


def self_test() -> dict[str, Any]:
    output = render("resolve", "zero-candidates", "candidate count equals one", 1, 0)
    context = output["additionalContext"]
    assert context.index("stage=") < context.index("code=") < context.index("condition=")
    assert context.index("expected=") < context.index("received=")
    assert output["diagnostic"]["expected"] == 1
    assert output["diagnostic"]["received"] == 0
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
    output = render(arguments.stage, arguments.code, arguments.condition, parse_json_value(arguments.expected), parse_json_value(arguments.received))
    if arguments.hook_only:
        output = {"additionalContext": output["additionalContext"]}
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
