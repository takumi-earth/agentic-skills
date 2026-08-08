#!/usr/bin/env python3
"""Print bounded, line-numbered source context around an exact text marker."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile


def atomic_create_text(path: Path, content: str) -> None:
    """Create a durable text report without overwriting prior evidence."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing context report: {path}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
        temporary.unlink()
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--context", type=int, default=18)
    parser.add_argument("--head", type=int, default=0)
    parser.add_argument("--needle")
    parser.add_argument("--expected-matches", type=int)
    parser.add_argument("--line", type=int, action="append", default=[])
    parser.add_argument("--related-needle", action="append", default=[])
    arguments = parser.parse_args()

    lines = arguments.source.read_text(encoding="utf-8").splitlines()
    output_lines = [f"source={arguments.source}"]
    if arguments.head:
        output_lines.append("source_head:")
        for index, line in enumerate(lines[: arguments.head]):
            output_lines.append(f" {index + 1:05d}: {line}")
    if arguments.expected_matches is not None and arguments.needle is None:
        parser.error("condition=--expected-matches requires --needle; received=no --needle")

    centers: list[int] = []
    for line_number in arguments.line:
        if not 1 <= line_number <= len(lines):
            parser.error(
                "line selection check failed; condition=1 <= line <= source line count; "
                f"expected=1..{len(lines)}; received={line_number}"
            )
        centers.append(line_number - 1)

    if arguments.needle is None and not centers:
        atomic_create_text(arguments.output, "\n".join(output_lines) + "\n")
        print(json.dumps({"output": str(arguments.output), "context_line_count": 0}))
        return 0

    matches: list[int] = []
    if arguments.needle is not None:
        matches = [index for index, line in enumerate(lines) if arguments.needle in line]
        if (
            arguments.expected_matches is not None
            and len(matches) != arguments.expected_matches
        ):
            raise SystemExit(
                "source match count check failed; "
                f"condition=line contains marker {arguments.needle!r}; "
                f"expected={arguments.expected_matches}; received={len(matches)}"
            )
        if not matches and arguments.expected_matches != 0:
            raise SystemExit(
                "source marker check failed; "
                f"condition=at least one line contains marker; "
                f"expected={arguments.needle!r}; received=0 matches"
            )
        output_lines.append(
            "match_lines=" + ",".join(str(index + 1) for index in matches)
        )
    if centers:
        output_lines.append(
            "selected_lines=" + ",".join(str(index + 1) for index in centers)
        )

    centers.extend(matches)
    emitted: set[int] = set()
    for center in sorted(set(centers)):
        start = max(0, center - arguments.context)
        end = min(len(lines), center + arguments.context + 1)
        for index in range(start, end):
            if index in emitted:
                continue
            emitted.add(index)
            marker = ">" if index == center else " "
            output_lines.append(f"{marker}{index + 1:05d}: {lines[index]}")

    related = [
        index
        for index, line in enumerate(lines)
        if any(needle in line for needle in arguments.related_needle)
    ]
    if arguments.related_needle:
        output_lines.append(
            "related_lines=" + ",".join(str(index + 1) for index in related)
        )
    atomic_create_text(arguments.output, "\n".join(output_lines) + "\n")
    print(
        json.dumps(
            {
                "output": str(arguments.output),
                "context_line_count": len(emitted),
                "match_count": len(matches),
                "selected_line_count": len(arguments.line),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
