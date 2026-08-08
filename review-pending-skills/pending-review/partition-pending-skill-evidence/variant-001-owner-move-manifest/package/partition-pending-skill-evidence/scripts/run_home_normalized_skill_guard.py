#!/usr/bin/env python3
"""Run the packaged skill scope guard while keeping persisted home paths as `~`."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any


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


def atomic_create(path: Path, payload: dict[str, Any]) -> None:
    path = path.expanduser().absolute()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite guard snapshot: {path}")
    encoded = (json.dumps(normalize(payload), indent=2, sort_keys=True) + "\n").encode()
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    if path.read_bytes() != encoded:
        raise RuntimeError(f"guard snapshot durability re-read mismatch: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guard", required=True, type=Path)
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    result = parser.parse_args()
    if result.arguments and result.arguments[0] == "--":
        result.arguments = result.arguments[1:]
    if not result.arguments:
        parser.error("guard arguments are required after --")
    return result


def main() -> int:
    arguments = parse_args()
    guard = arguments.guard.expanduser().resolve(strict=True)
    command_arguments = list(arguments.arguments)
    output_path: Path | None = None
    intermediate_path: Path | None = None

    if command_arguments[0] == "snapshot":
        try:
            output_index = command_arguments.index("--output") + 1
            output_path = Path(command_arguments[output_index]).expanduser().absolute()
        except (ValueError, IndexError) as error:
            raise SystemExit("snapshot requires `--output <path>`") from error
        output_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, intermediate_name = tempfile.mkstemp(
            prefix=f".{output_path.name}.guard.", dir=output_path.parent
        )
        os.close(descriptor)
        intermediate_path = Path(intermediate_name)
        intermediate_path.unlink()
        command_arguments[output_index] = str(intermediate_path)

    completed = subprocess.run(
        ["python3", str(guard), *command_arguments],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )

    try:
        if completed.returncode == 0 and output_path is not None and intermediate_path is not None:
            payload = json.loads(intermediate_path.read_text(encoding="utf-8"))
            atomic_create(output_path, payload)
        print(normalize(completed.stdout), end="")
        if completed.stderr:
            import sys

            print(normalize(completed.stderr), end="", file=sys.stderr)
        return completed.returncode
    finally:
        if intermediate_path is not None:
            intermediate_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
