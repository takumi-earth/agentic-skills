#!/usr/bin/env python3
"""Resolve exact skill projections without scanning or mutating roots."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any


class TopologyError(Exception):
    """Describe an invalid skill projection."""


def display_path(path: Path) -> str:
    """Render a path with a home-relative prefix where possible."""

    resolved = path.expanduser().absolute()
    home = Path.home().resolve()
    try:
        relative = resolved.relative_to(home)
    except ValueError:
        return str(resolved)
    return "~" if not relative.parts else f"~/{relative.as_posix()}"


def parse_projection(value: str) -> tuple[str, Path]:
    """Parse one LABEL=PATH projection."""

    label, separator, raw_path = value.partition("=")
    if not separator or not label or not raw_path:
        raise TopologyError(f"invalid projection {value!r}; expected LABEL=PATH")
    return label, Path(raw_path).expanduser().absolute()


def inspect_projection(label: str, lexical: Path) -> dict[str, Any]:
    """Inspect one exact package or body projection."""

    if not lexical.exists() and not lexical.is_symlink():
        raise TopologyError(f"projection does not exist: {display_path(lexical)}")
    package = lexical if lexical.name != "SKILL.md" else lexical.parent
    body = lexical if lexical.name == "SKILL.md" else lexical / "SKILL.md"
    if not body.is_file():
        raise TopologyError(f"projection lacks SKILL.md: {display_path(package)}")
    resolved_body = body.resolve()
    content = resolved_body.read_bytes()
    stat = resolved_body.stat()
    return {
        "body_sha256": hashlib.sha256(content).hexdigest(),
        "canonical_body": display_path(resolved_body),
        "filesystem_identity": {"device": stat.st_dev, "inode": stat.st_ino},
        "label": label,
        "lexical_path": display_path(lexical),
        "projection_is_symlink": lexical.is_symlink() or package.is_symlink(),
        "symlink_target": os.readlink(lexical if lexical.is_symlink() else package)
        if lexical.is_symlink() or package.is_symlink()
        else None,
    }


def main() -> int:
    """Render topology for caller-supplied projections."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection", action="append", required=True)
    arguments = parser.parse_args()
    try:
        parsed = [parse_projection(value) for value in arguments.projection]
        labels = [label for label, _ in parsed]
        if len(labels) != len(set(labels)):
            raise TopologyError("projection labels must be unique")
        projections = [inspect_projection(label, path) for label, path in parsed]
    except (OSError, UnicodeError, TopologyError) as error:
        print(f"skill-topology resolution failed: {error}", file=sys.stderr)
        return 2
    groups: dict[str, list[str]] = {}
    for projection in projections:
        groups.setdefault(projection["body_sha256"], []).append(projection["label"])
    report = {
        "content_groups": [
            {"body_sha256": digest, "labels": sorted(labels)}
            for digest, labels in sorted(groups.items())
        ],
        "projections": sorted(projections, key=lambda item: item["label"]),
        "schema_version": 1,
    }
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
