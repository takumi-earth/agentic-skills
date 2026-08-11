#!/usr/bin/env python3
"""Run declared skill validators without a shell and preserve each outcome."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def validate_plan(document: Any) -> list[str]:
    if not isinstance(document, dict):
        return ["plan must be an object"]
    errors: list[str] = []
    if document.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    packages = document.get("packages")
    if not isinstance(packages, list) or not packages or any(not isinstance(item, str) or not item for item in packages):
        errors.append("packages must be a nonempty string array")
    validators = document.get("validators")
    if not isinstance(validators, list) or not validators:
        return errors + ["validators must be a nonempty array"]
    seen: set[str] = set()
    for index, validator in enumerate(validators):
        prefix = f"validators[{index}]"
        if not isinstance(validator, dict):
            errors.append(f"{prefix} must be an object")
            continue
        identifier = validator.get("id")
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"{prefix}.id must be a nonempty string")
        elif identifier in seen:
            errors.append(f"{prefix}.id is duplicated")
        else:
            seen.add(identifier)
        if validator.get("kind") not in {"canonical", "harness", "supplemental"}:
            errors.append(f"{prefix}.kind is invalid")
        if not isinstance(validator.get("required"), bool):
            errors.append(f"{prefix}.required must be boolean")
        command = validator.get("command")
        if not isinstance(command, list) or not command or any(not isinstance(item, str) or not item for item in command):
            errors.append(f"{prefix}.command must be a nonempty string array")
        interpreter = validator.get("interpreter")
        if interpreter is not None and (not isinstance(interpreter, str) or not interpreter):
            errors.append(f"{prefix}.interpreter must be null or a nonempty string")
    max_output = document.get("max_output_bytes", 20000)
    if not isinstance(max_output, int) or isinstance(max_output, bool) or max_output < 1:
        errors.append("max_output_bytes must be a positive integer")
    timeout = document.get("timeout_seconds", 120)
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        errors.append("timeout_seconds must be positive")
    return errors


def bound_text(value: str, limit: int) -> dict[str, Any]:
    encoded = value.encode("utf-8")
    emitted = encoded[:limit]
    while emitted:
        try:
            text = emitted.decode("utf-8")
            break
        except UnicodeDecodeError:
            emitted = emitted[:-1]
    else:
        text = ""
    return {
        "text": text,
        "original_bytes": len(encoded),
        "emitted_bytes": len(emitted),
        "omitted_bytes": len(encoded) - len(emitted),
    }


def timeout_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def inner_assertions(stdout: str, stderr: str) -> str:
    combined = f"{stdout}\n{stderr}".lower()
    if "assertions: failed" in combined:
        return "failed"
    if "assertions: passed" in combined:
        return "passed"
    return "not-reported"


def command_for(validator: dict[str, Any], package: str) -> list[str]:
    command = [argument.replace("{package}", package) for argument in validator["command"]]
    if validator.get("interpreter"):
        command = [validator["interpreter"], *command]
    return command


def run(plan_path: Path, document: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    max_output = document.get("max_output_bytes", 20000)
    timeout = document.get("timeout_seconds", 120)
    working_directory_value = document.get("working_directory")
    working_directory = (
        Path(working_directory_value).resolve()
        if isinstance(working_directory_value, str)
        else plan_path.parent.resolve()
    )
    results: list[dict[str, Any]] = []
    for package in document["packages"]:
        for validator in document["validators"]:
            command = command_for(validator, package)
            started = time.monotonic()
            result: dict[str, Any] = {
                "validator_id": validator["id"],
                "kind": validator["kind"],
                "required": validator["required"],
                "package": package,
                "command": command,
                "start_state": "started",
                "exit_code": None,
                "timed_out": False,
            }
            try:
                completed = subprocess.run(
                    command,
                    cwd=working_directory,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                result["exit_code"] = completed.returncode
                result["stdout"] = bound_text(completed.stdout, max_output)
                result["stderr"] = bound_text(completed.stderr, max_output)
                result["inner_assertions"] = inner_assertions(completed.stdout, completed.stderr)
            except FileNotFoundError as error:
                result["start_state"] = "unavailable"
                result["error"] = str(error)
                result["stdout"] = bound_text("", max_output)
                result["stderr"] = bound_text("", max_output)
                result["inner_assertions"] = "not-reported"
            except subprocess.TimeoutExpired as error:
                result["timed_out"] = True
                result["exit_code"] = None
                result["stdout"] = bound_text(timeout_text(error.stdout), max_output)
                result["stderr"] = bound_text(timeout_text(error.stderr), max_output)
                result["inner_assertions"] = "not-reported"
            result["duration_ms"] = round((time.monotonic() - started) * 1000, 3)
            result["process_passed"] = result["exit_code"] == 0
            results.append(result)
    required_failures = [
        result
        for result in results
        if result["required"] and (result["start_state"] != "started" or result["exit_code"] != 0)
    ]
    return (0 if not required_failures else 1), {
        "schema_version": 1,
        "status": "passed" if not required_failures else "failed",
        "required_failure_count": len(required_failures),
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    args = parser.parse_args(argv)
    try:
        document = json.loads(args.plan.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "invalid-input", "errors": [str(error)]}, sort_keys=True))
        return 2
    errors = validate_plan(document)
    if errors:
        print(json.dumps({"status": "invalid", "errors": errors}, sort_keys=True))
        return 2
    code, report = run(args.plan, document)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
