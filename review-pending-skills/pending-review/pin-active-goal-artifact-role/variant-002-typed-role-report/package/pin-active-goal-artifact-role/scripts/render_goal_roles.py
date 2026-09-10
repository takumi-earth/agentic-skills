#!/usr/bin/env python3
"""Render roles for one exact active goal and caller-supplied references."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
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


def reference_lines(text: str, path: Path, active: Path) -> list[int]:
    """Match complete path spellings; resolve authored relative paths from the goal."""
    relative = os.path.relpath(path, active.parent)
    spellings = {str(path), display_path(path), relative, f"./{relative}"}
    alternatives = "|".join(re.escape(value) for value in sorted(spellings))
    pattern = re.compile(r"(?<![^\s`\"'<>(\[=:])(?:" + alternatives + r")(?=$|[\s`\"'<>),;\]])")
    return [number for number, line in enumerate(text.split("\n"), 1) if pattern.search(line)]


def display_error(error: Exception) -> str:
    home = re.escape(str(Path.home().resolve()))
    return re.sub(r"(?<![^\s`\"'<>(\[=:])" + home + r"(?=/|$)", "~", str(error))


def build_report(active_raw: str, reference_values: list[str]) -> dict[str, object]:
    """Build one role report without discovering any sibling paths."""

    active = Path(active_raw).expanduser().resolve()
    if not active.is_file():
        raise RoleError(f"active goal is not a readable file: {display_path(active)}")
    source = active.read_bytes()
    text = source.decode("utf-8")
    seen = {active}
    references: list[dict[str, object]] = []
    for value in reference_values:
        role, path = parse_reference(value)
        if path in seen:
            raise RoleError(f"artifact has duplicate or conflicting roles: {display_path(path)}")
        seen.add(path)
        rendered = display_path(path)
        matches = reference_lines(text, path, active)
        if not matches:
            raise RoleError(
                "secondary artifact is not explicitly referenced by the active goal: "
                f"role={role}; path={rendered}"
            )
        references.append({"path": rendered, "role": role, "role_source": "caller-declared",
                           "text_reference_verified": True, "reference_lines": matches,
                           "artifact_contents_verified": False})
    references.sort(key=lambda item: (item["role"], item["path"]))
    return {
        "active": {"path": display_path(active), "role": "active", "role_source": "caller-declared",
                   "sha256": hashlib.sha256(source).hexdigest()},
        "references": references,
        "status_authority": display_path(active),
        "status_authority_source": "caller-designation; not independently verified",
    }


def main() -> int:
    """Parse arguments and emit the role report."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--active", required=True)
    parser.add_argument("--reference", action="append", default=[])
    arguments = parser.parse_args()
    try:
        report = build_report(arguments.active, arguments.reference)
    except (OSError, ValueError, RuntimeError, RoleError) as error:
        print(f"artifact-role report failed: {display_error(error)}", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
