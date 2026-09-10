#!/usr/bin/env python3
"""Run the packaged skill scope guard while keeping persisted home paths as `~`."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
import subprocess
import tempfile
from typing import Any


USER_HOME = str(Path.home().resolve())


def normalize(value: Any) -> Any:
    if isinstance(value, str):
        if value == USER_HOME:
            return "~"
        return re.sub(re.escape(USER_HOME) + r"(?=$|[/\s\x27\x22:,)])", "~", value)
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {normalize(str(key)): normalize(item) for key, item in value.items()}
    return value


def atomic_create(path: Path, payload: dict[str, Any]) -> None:
    path = path.expanduser().absolute()
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path):
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


def option(arguments, flag):
    selected = None
    for index, value in enumerate(arguments):
        if value.startswith(flag + '='):
            selected = (index, value[len(flag) + 1:], True)
        elif value == flag:
            if index + 1 >= len(arguments) or arguments[index + 1].startswith('--'):
                raise ValueError(f'{flag} requires a value')
            selected = (index + 1, arguments[index + 1], False)
    if selected is None or not selected[1]:
        raise ValueError(f'{flag} requires a nonempty value')
    return selected


def snapshot_output(arguments):
    index, raw, inline = option(arguments, '--output')
    output = Path(os.path.abspath(Path(raw).expanduser()))
    _, root, _ = option(arguments, '--skills-root')
    scratch = (Path(root).expanduser().resolve(strict=True) / '.scratchpad').resolve()
    resolved = output.resolve(strict=False)
    if resolved == scratch or not resolved.is_relative_to(scratch):
        raise ValueError('snapshot output must be beneath the selected skills root scratchpad')
    if os.path.lexists(output):
        raise FileExistsError(f'refusing to overwrite guard snapshot: {output}')
    return index, output, inline


def run_guard(arguments):
    command_arguments = list(arguments.arguments)
    intermediate_path = None
    try:
        guard = arguments.guard.expanduser().resolve(strict=True)
        output_path = None
        if command_arguments[0] == 'snapshot':
            index, output_path, inline = snapshot_output(command_arguments)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, name = tempfile.mkstemp(prefix=f'.{output_path.name}.guard.', dir=output_path.parent)
            os.close(descriptor)
            intermediate_path = Path(name)
            command_arguments[index] = ('--output=' if inline else '') + str(intermediate_path)
        completed = subprocess.run(['python3', str(guard), *command_arguments], stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, text=True)
        if completed.returncode == 0 and output_path is not None:
            payload = json.loads(intermediate_path.read_text(encoding='utf-8'))
            atomic_create(output_path, payload)
        return completed
    finally:
        if intermediate_path is not None:
            intermediate_path.unlink(missing_ok=True)


def main() -> int:
    try:
        completed = run_guard(parse_args())
    except (OSError, ValueError, RuntimeError, RecursionError) as error:
        print(json.dumps(dict(status='adapter-failure', code='snapshot-conflict' if isinstance(error, FileExistsError) else 'adapter-error', error=normalize(str(error))), sort_keys=True))
        return 2
    print(normalize(completed.stdout), end='')
    print(normalize(completed.stderr), end='', file=sys.stderr)
    return completed.returncode


if __name__ == '__main__':
    raise SystemExit(main())
