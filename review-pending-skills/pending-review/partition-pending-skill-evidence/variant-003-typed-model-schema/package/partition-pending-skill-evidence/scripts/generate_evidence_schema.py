#!/usr/bin/env python3
"""Generate the pending evidence-record JSON Schema deterministically."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
from typing import Any


def schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "skill://partition-pending-skill-evidence/evidence-record.schema.json",
        "title": "Automatic skill evidence record",
        "type": "object",
        "required": ["schema_version", "event_id", "event_type", "status"],
        "properties": {
            "schema_version": {"const": 1},
            "event_id": {"type": "string", "minLength": 1},
            "event_type": {"type": "string", "minLength": 1},
            "status": {"type": "string", "minLength": 1},
            "condition": {"type": "string"},
            "expected": {},
            "received": {},
            "evidence": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": True,
    }


def encoded() -> str:
    return json.dumps(schema(), indent=2, sort_keys=True) + "\n"


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temporary:
        output = Path(temporary) / "schema.json"
        output.write_text(encoded(), encoding="utf-8")
        first = output.read_text(encoding="utf-8")
        second = encoded()
        parsed = json.loads(first)
        assert first == second
        assert parsed["properties"]["schema_version"] == {"const": 1}
        assert set(parsed["required"]) == {"schema_version", "event_id", "event_type", "status"}
        assert parsed["additionalProperties"] is True
    return {"status": "passed", "assertions": 4}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if not arguments.self_test and arguments.output is None:
        parser.error("--output is required unless --self-test is used")
    return arguments


def main() -> int:
    arguments = parse_args()
    if arguments.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return 0
    expected = encoded()
    output = arguments.output.expanduser()
    if arguments.check:
        received = output.read_text(encoding="utf-8") if output.is_file() else None
        if received != expected:
            print(
                json.dumps(
                    {
                        "status": "failure",
                        "condition": "generated schema equals persisted schema",
                        "expected": expected,
                        "received": received,
                    },
                    sort_keys=True,
                )
            )
            return 1
        print(json.dumps({"status": "valid", "output": str(output)}, sort_keys=True))
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(expected, encoding="utf-8")
    print(json.dumps({"status": "written", "output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
