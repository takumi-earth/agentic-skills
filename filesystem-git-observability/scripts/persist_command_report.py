#!/usr/bin/env python3
"""Run a command without a shell and persist its complete result atomically.

This driver exists so the diagnostic invocation, its exact command, its exit
status, and its complete output are retained as an auditable artifact without
shell redirection or an ad hoc command pipeline.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_report(stdout: str) -> dict[str, object]:
    opening = stdout.find("{")
    if opening < 0:
        raise ValueError("diagnostic stdout did not contain a JSON object")
    value = json.loads(stdout[opening:])
    if not isinstance(value, dict):
        raise ValueError("diagnostic JSON root was not an object")
    return value


def atomic_create_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(
            f"refusing to overwrite existing audit artifact: {path}"
        )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, 0o600)
        os.link(temporary_path, path)
        temporary_path.unlink()
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--input", type=Path, action="append", default=[])
    parser.add_argument("--parse-json", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    arguments = parser.parse_args()

    command = list(arguments.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("a command is required after `--`")
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    input_sha256_before = {
        str(path): sha256_file(path) for path in sorted(arguments.input)
    }
    started_output = arguments.output.with_name(arguments.output.name + ".started.json")
    existing_outputs = [
        str(path) for path in (arguments.output, started_output) if path.exists()
    ]
    if existing_outputs:
        raise FileExistsError(
            "command audit output precondition failed; "
            "condition=final and write-ahead paths are both absent; "
            f"expected=[]; received={existing_outputs}"
        )
    write_ahead = {
        "schema_version": 1,
        "state": "started",
        "purpose": arguments.purpose,
        "started_at_utc": started,
        "command": command,
        "input_sha256_before": input_sha256_before,
        "intended_final_artifact": str(arguments.output),
    }
    atomic_create_json(started_output, write_ahead)
    write_ahead_sha256 = sha256_file(started_output)
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    finished = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    input_sha256_after = {
        str(path): sha256_file(path) for path in sorted(arguments.input)
    }

    parsed_report: dict[str, object] | None = None
    parse_error: str | None = None
    if arguments.parse_json:
        try:
            parsed_report = parse_report(completed.stdout)
        except (ValueError, json.JSONDecodeError) as error:
            parse_error = f"{type(error).__name__}: {error}"

    artifact: dict[str, object] = {
        "schema_version": 1,
        "purpose": arguments.purpose,
        "started_at_utc": started,
        "finished_at_utc": finished,
        "command": command,
        "write_ahead_artifact": str(started_output),
        "write_ahead_sha256": write_ahead_sha256,
        "input_sha256_before": input_sha256_before,
        "input_sha256_after": input_sha256_after,
        "exit_code": completed.returncode,
        "stderr": completed.stderr,
        "stdout": completed.stdout,
        "report_parse_error": parse_error,
        "report": parsed_report,
    }
    atomic_create_json(arguments.output, artifact)

    summary = {
        "audit_artifact": str(arguments.output),
        "exit_code": completed.returncode,
        "report_parsed": parsed_report is not None if arguments.parse_json else None,
        "input_sha256_before": input_sha256_before,
        "input_sha256_after": input_sha256_after,
        "write_ahead_artifact": str(started_output),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    if completed.returncode != 0:
        return completed.returncode
    return 0 if not arguments.parse_json or parsed_report is not None else 5


if __name__ == "__main__":
    raise SystemExit(main())
