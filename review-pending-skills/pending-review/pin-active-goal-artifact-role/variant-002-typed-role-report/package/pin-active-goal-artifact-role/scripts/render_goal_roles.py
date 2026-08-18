#!/usr/bin/env python3
"""Render roles for one exact active goal and caller-supplied references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ALLOWED_ROLES = {"historical", "evidence"}


class RoleError(Exception):
    """Describe an invalid or unsupported artifact-role request."""


def display_path(path: Path) -> str:
    """Render a resolved path without expanding the user's home in output."""

    resolved = path.expanduser().resolve()
    home = Path.home().resolve()
    try:
        relative = resolved.relative_to(home)
    except ValueError:
        return str(resolved)
    return "~" if not relative.parts else f"~/{relative.as_posix()}"


def parse_reference(value: str) -> tuple[str, Path]:
    """Parse one ROLE=PATH reference."""

    role, separator, raw_path = value.partition("=")
    if not separator or role not in ALLOWED_ROLES or not raw_path:
        expected = "historical=<path> or evidence=<path>"
        raise RoleError(f"invalid reference {value!r}; expected {expected}")
    return role, Path(raw_path).expanduser().resolve()


def build_report(active_raw: str, reference_values: list[str]) -> dict[str, object]:
    """Build one role report without discovering any sibling paths."""

    active = Path(active_raw).expanduser().resolve()
    if not active.is_file():
        raise RoleError(f"active goal is not a readable file: {display_path(active)}")
    text = active.read_text(encoding="utf-8")
    seen = {active}
    references: list[dict[str, str]] = []
    for value in reference_values:
        role, path = parse_reference(value)
        if path in seen:
            raise RoleError(f"artifact has duplicate or conflicting roles: {display_path(path)}")
        seen.add(path)
        rendered = display_path(path)
        expanded = str(path)
        if rendered not in text and expanded not in text:
            raise RoleError(
                "secondary artifact is not explicitly referenced by the active goal: "
                f"role={role}; path={rendered}"
            )
        references.append({"path": rendered, "role": role})
    references.sort(key=lambda item: (item["role"], item["path"]))
    return {
        "active": {"path": display_path(active), "role": "active"},
        "references": references,
        "status_authority": display_path(active),
    }


def main() -> int:
    """Parse arguments and emit the role report."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--active", required=True)
    parser.add_argument("--reference", action="append", default=[])
    arguments = parser.parse_args()
    try:
        report = build_report(arguments.active, arguments.reference)
    except (OSError, UnicodeError, RoleError) as error:
        print(f"artifact-role report failed: {error}", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
