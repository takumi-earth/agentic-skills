#!/usr/bin/env python3
"""Inspect current caller-selected skill projections without scanning skill roots."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any


class TopologyError(Exception):
    """Describe an invalid skill projection."""


def display_path(path: Path) -> str:
    lexical = path.expanduser().absolute()
    try:
        relative = lexical.relative_to(Path.home())
    except ValueError:
        return str(lexical)
    return "~" if not relative.parts else f"~/{relative.as_posix()}"


def parse_projection(value: str) -> tuple[str, Path]:
    label, separator, raw_path = value.partition("=")
    if not separator or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]*", label) is None or not raw_path:
        raise TopologyError("expected LABEL=PATH with a unique identifier label")
    return label, Path(raw_path).expanduser().absolute()


def inspect_projection(label: str, lexical: Path) -> dict[str, Any]:
    body = lexical if lexical.name == "SKILL.md" else lexical / "SKILL.md"
    if not body.is_file():
        raise TopologyError(f"projection lacks a readable SKILL.md: {display_path(lexical)}")
    canonical = body.resolve(strict=True)
    with canonical.open("rb") as handle:
        content = handle.read()
        stat = os.fstat(handle.fileno())
    links = []
    for component in [*reversed(body.parents), body]:
        if component.is_symlink():
            target = os.readlink(component)
            links.append({
                "path": display_path(component),
                "target": display_path(Path(target)) if Path(target).is_absolute() else target,
            })
    return {
        "label": label,
        "lexical_path": display_path(lexical),
        "lexical_symlinks": links,
        "canonical_body": display_path(canonical),
        "filesystem_identity": {"device": stat.st_dev, "inode": stat.st_ino},
        "body_sha256": hashlib.sha256(content).hexdigest(),
    }


def resolve(values: list[str]) -> dict[str, Any]:
    parsed = [parse_projection(value) for value in values]
    labels = [label for label, _ in parsed]
    if len(labels) != len(set(labels)):
        raise TopologyError("projection labels must be unique")
    projections = [inspect_projection(label, path) for label, path in parsed]
    groups: dict[str, list[str]] = {}
    for projection in projections:
        groups.setdefault(projection["body_sha256"], []).append(projection["label"])
    return {
        "schema_version": 1,
        "projections": sorted(projections, key=lambda item: item["label"]),
        "content_groups": [
            {"body_sha256": digest, "labels": sorted(labels)}
            for digest, labels in sorted(groups.items())
        ],
        "evidence_limits": {"time_scope": "current", "content_scope": "SKILL.md"},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection", action="append", required=True)
    arguments = parser.parse_args()
    try:
        report = resolve(arguments.projection)
    except (OSError, UnicodeError, ValueError, RuntimeError, TopologyError) as error:
        detail = str(error).replace(str(Path.home()), "~")
        print(f"skill-topology resolution failed: {detail}", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
