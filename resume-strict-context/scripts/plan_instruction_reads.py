#!/usr/bin/env python3
"""Batch-plan byte-bounded, non-overlapping reads without emitting contents."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence


DEFAULT_MAX_CHUNK_BYTES = 12_000


def display_path(path: Path) -> str:
    """Render a path relatively when supplied that way, otherwise normalize home."""

    if not path.is_absolute():
        return path.as_posix()
    home = Path.home().resolve(strict=False)
    absolute = path.absolute()
    try:
        return f"~/{absolute.relative_to(home).as_posix()}"
    except ValueError:
        return absolute.as_posix()


def logical_lines(data: bytes, path: Path) -> list[bytes]:
    """Return UTF-8 logical lines, including an unterminated final line."""

    try:
        data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"instruction file is not UTF-8: {display_path(path)}") from error
    return data.splitlines(keepends=True)


def chunk_lines(lines: Sequence[bytes], max_chunk_bytes: int) -> list[dict[str, Any]]:
    """Partition complete logical lines without exceeding the byte target when possible."""

    chunks: list[dict[str, Any]] = []
    start_line = 1
    current_bytes = 0
    current_count = 0

    def finish(*, oversized_line: bool = False) -> None:
        nonlocal start_line, current_bytes, current_count
        if current_count == 0:
            return
        chunks.append(
            {
                "start_line": start_line,
                "end_line": start_line + current_count - 1,
                "byte_count": current_bytes,
                "oversized_line": oversized_line,
            }
        )
        start_line += current_count
        current_bytes = 0
        current_count = 0

    for line in lines:
        line_bytes = len(line)
        if current_count and current_bytes + line_bytes > max_chunk_bytes:
            finish()
        current_bytes += line_bytes
        current_count += 1
        if line_bytes > max_chunk_bytes:
            finish(oversized_line=True)
    finish()
    return chunks


def plan_file(path: Path, max_chunk_bytes: int) -> dict[str, Any]:
    """Build one immutable read plan for a regular instruction file."""

    if not path.is_file():
        raise ValueError(f"instruction path is not a regular file: {display_path(path)}")
    data = path.read_bytes()
    lines = logical_lines(data, path)
    chunks = chunk_lines(lines, max_chunk_bytes)
    return {
        "path": display_path(path),
        "resolved_path": display_path(path.resolve(strict=True)),
        "sha256": hashlib.sha256(data).hexdigest(),
        "byte_count": len(data),
        "logical_line_count": len(lines),
        "ends_with_newline": data.endswith(b"\n"),
        "chunks": chunks,
        "has_oversized_line": any(chunk["oversized_line"] for chunk in chunks),
    }


def build_plan(paths: Sequence[Path], max_chunk_bytes: int) -> dict[str, Any]:
    """Build a metadata-only plan and reject duplicate lexical inputs."""

    if max_chunk_bytes < 1:
        raise ValueError("max chunk bytes must be positive")
    lexical = [path.absolute() for path in paths]
    if len(set(lexical)) != len(lexical):
        raise ValueError("instruction paths must be unique")
    return {
        "schema_version": 1,
        "max_chunk_bytes": max_chunk_bytes,
        "file_count": len(paths),
        "files": [plan_file(path, max_chunk_bytes) for path in paths],
        "content_emitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Preflight every selected instruction file in one metadata-only batch; "
            "the resulting ranges must still be read one file at a time."
        )
    )
    parser.add_argument(
        "--max-chunk-bytes",
        type=int,
        default=DEFAULT_MAX_CHUNK_BYTES,
    )
    parser.add_argument(
        "paths",
        type=Path,
        nargs="+",
        help="instruction paths to preflight together without emitting their bodies",
    )
    arguments = parser.parse_args()
    try:
        plan = build_plan(arguments.paths, arguments.max_chunk_bytes)
    except (OSError, ValueError) as error:
        parser.exit(2, f"READ_PLAN_ERROR: {error}\n")
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
