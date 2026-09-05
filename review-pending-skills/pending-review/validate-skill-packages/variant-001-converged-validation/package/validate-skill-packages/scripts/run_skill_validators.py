#!/usr/bin/env python3
"""Run declared validators with independent process and assertion outcomes."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def present(value: Any) -> Any:
    if isinstance(value, str):
        home = str(Path.home())
        return "~" if value == home else value.replace(home + "/", "~/")
    if isinstance(value, list):
        return [present(item) for item in value]
    if isinstance(value, dict):
        return {key: present(item) for key, item in value.items()}
    return value


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_array(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(nonempty(item) for item in value)


def validate_plan(document: Any) -> list[str]:
    if not isinstance(document, dict):
        return ["plan must be an object"]
    errors: list[str] = []
    if type(document.get("schema_version")) is not int or document["schema_version"] != 1:
        errors.append("schema_version must equal 1")
    if not string_array(document.get("packages")):
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
        if not nonempty(identifier):
            errors.append(f"{prefix}.id must be a nonempty string")
        elif identifier in seen:
            errors.append(f"{prefix}.id is duplicated")
        else:
            seen.add(identifier)
        kind = validator.get("kind")
        if not isinstance(kind, str) or kind not in {"canonical", "harness", "supplemental"}:
            errors.append(f"{prefix}.kind is invalid")
        if not isinstance(validator.get("required"), bool):
            errors.append(f"{prefix}.required must be boolean")
        if not string_array(validator.get("command")):
            errors.append(f"{prefix}.command must be a nonempty string array")
        interpreter = validator.get("interpreter")
        if interpreter is not None and not nonempty(interpreter):
            errors.append(f"{prefix}.interpreter must be null or a nonempty string")
    max_output = document.get("max_output_bytes", 20000)
    if type(max_output) is not int or max_output < 1:
        errors.append("max_output_bytes must be a positive integer")
    timeout = document.get("timeout_seconds", 120)
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        errors.append("timeout_seconds must be finite and positive")
    if "working_directory" in document and not nonempty(document["working_directory"]):
        errors.append("working_directory must be a nonempty string")
    return errors


def working_directory(plan_path: Path, document: dict[str, Any]) -> Path:
    directory = Path(document.get("working_directory", ".")).expanduser()
    if not directory.is_absolute():
        directory = plan_path.expanduser().resolve().parent / directory
    return directory.resolve()


def bound_output(value: bytes | None, limit: int) -> dict[str, Any]:
    original = value or b""
    emitted = original[:limit]
    return {
        "text": emitted.decode("utf-8", errors="replace"),
        "original_bytes": len(original),
        "emitted_bytes": len(emitted),
        "omitted_bytes": len(original) - len(emitted),
    }


def inner_assertions(stdout: bytes, stderr: bytes) -> str:
    lines = {line.strip().lower() for line in (stdout + b"\n" + stderr).splitlines()}
    if b"assertions: failed" in lines:
        return "failed"
    if b"assertions: passed" in lines:
        return "passed"
    return "not-reported"


def expand_argument(argument: str) -> str:
    return str(Path(argument).expanduser()) if argument.startswith("~/") else argument


def command_for(validator: dict[str, Any], package: str) -> list[str]:
    command = [argument.replace("{package}", package) for argument in validator["command"]]
    if validator.get("interpreter"):
        command = [validator["interpreter"], *command]
    return [expand_argument(argument) for argument in command]


def emit_progress(event: str, origin: float, position: int, total: int, result: dict[str, Any]) -> None:
    record = {
        "event": event,
        "position": position,
        "total": total,
        "validator_id": result["validator_id"],
        "package": result["package"],
        "elapsed_ms": round((time.monotonic() - origin) * 1000, 3),
    }
    if event == "validator-finished":
        record.update({
            "start_state": result["start_state"],
            "exit_code": result["exit_code"],
            "check_passed": result["check_passed"],
        })
    print(json.dumps(present(record), sort_keys=True), file=sys.stderr, flush=True)


def run(plan_path: Path, document: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    directory = working_directory(plan_path, document)
    if not directory.is_dir():
        return 2, {"status": "invalid", "errors": [f"working directory is unavailable: {directory}"]}
    limit = document.get("max_output_bytes", 20000)
    timeout = document.get("timeout_seconds", 120)
    results: list[dict[str, Any]] = []
    origin = time.monotonic()
    total = len(document["packages"]) * len(document["validators"])
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
            position = len(results) + 1
            emit_progress("validator-starting", origin, position, total, result)
            stdout = stderr = b""
            try:
                completed = subprocess.run(
                    command, cwd=directory, check=False, capture_output=True,
                    timeout=timeout,
                )
                result["exit_code"] = completed.returncode
                stdout, stderr = completed.stdout, completed.stderr
            except FileNotFoundError as error:
                result["start_state"] = "unavailable"
                result["error"] = str(error)
            except OSError as error:
                result["start_state"] = "error"
                result["error"] = str(error)
            except subprocess.TimeoutExpired as error:
                result["timed_out"] = True
                stdout, stderr = error.stdout or b"", error.stderr or b""
            result["stdout"] = bound_output(stdout, limit)
            result["stderr"] = bound_output(stderr, limit)
            result["inner_assertions"] = inner_assertions(stdout, stderr)
            result["duration_ms"] = round((time.monotonic() - started) * 1000, 3)
            result["process_passed"] = result["exit_code"] == 0
            result["check_passed"] = (
                result["process_passed"] and result["inner_assertions"] != "failed"
            )
            emit_progress("validator-finished", origin, position, total, result)
            results.append(result)
    failures = [result for result in results if result["required"] and not result["check_passed"]]
    return (1 if failures else 0), {
        "schema_version": 1,
        "status": "failed" if failures else "passed",
        "required_failure_count": len(failures),
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    args = parser.parse_args(argv)
    try:
        document = json.loads(args.plan.expanduser().read_bytes())
    except (OSError, ValueError) as error:
        print(json.dumps(present({"status": "invalid-input", "errors": [str(error)]})))
        return 2
    errors = validate_plan(document)
    if errors:
        print(json.dumps({"status": "invalid", "errors": errors}, sort_keys=True))
        return 2
    code, report = run(args.plan, document)
    print(json.dumps(present(report), indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
