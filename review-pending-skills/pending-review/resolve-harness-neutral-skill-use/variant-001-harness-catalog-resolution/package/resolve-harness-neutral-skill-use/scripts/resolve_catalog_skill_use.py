#!/usr/bin/env python3
"""Resolve skill reference and read evidence from a harness catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterator


READ_COMMAND = re.compile(r"\b(?:sed|head|tail|less|more|awk|perl|python\d*|rg)\b")


class ResolveError(Exception):
    """Describe malformed catalog or rollout evidence."""


def display_path(raw: str) -> str:
    """Normalize one path beneath the user home for output."""

    path = Path(raw).expanduser().resolve(strict=False)
    home = Path.home().resolve()
    try:
        relative = path.relative_to(home)
    except ValueError:
        return str(path)
    return "~" if not relative.parts else f"~/{relative.as_posix()}"


def string_leaves(value: Any) -> Iterator[str]:
    """Yield strings from one typed content structure."""

    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from string_leaves(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from string_leaves(item)


def load_catalog(path: Path) -> dict[str, dict[str, Any]]:
    """Load unique skill names and their exact body paths."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_skills = payload.get("skills") if isinstance(payload, dict) else None
    if not isinstance(raw_skills, list):
        raise ResolveError("catalog must contain a skills array")
    skills: dict[str, dict[str, Any]] = {}
    for raw in raw_skills:
        if not isinstance(raw, dict):
            raise ResolveError("every catalog skill must be an object")
        name = raw.get("name")
        path_value = raw.get("path")
        if not isinstance(name, str) or not name or not isinstance(path_value, str) or not path_value:
            raise ResolveError("every catalog skill needs nonempty name and path")
        if name in skills:
            raise ResolveError(f"duplicate catalog skill: {name}")
        skills[name] = {
            "assistant_reference_lines": [],
            "body_read_command_lines": [],
            "path": display_path(path_value),
            "path_forms": {path_value, str(Path(path_value).expanduser().resolve(strict=False)), display_path(path_value)},
        }
    return skills


def resolve(catalog_path: Path, transcript_path: Path) -> dict[str, Any]:
    """Classify catalog-backed evidence in one rollout."""

    skills = load_catalog(catalog_path)
    with transcript_path.open(encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as error:
                raise ResolveError(f"malformed JSON at line {line_number}: {error}") from error
            if record.get("type") != "response_item" or not isinstance(record.get("payload"), dict):
                continue
            payload = record["payload"]
            if payload.get("type") == "message" and payload.get("role") == "assistant":
                message = "\n".join(string_leaves(payload.get("content")))
                for name, evidence in skills.items():
                    if re.search(rf"\${re.escape(name)}\b", message):
                        evidence["assistant_reference_lines"].append(line_number)
            if payload.get("type") != "custom_tool_call" or payload.get("name") != "exec":
                continue
            source = payload.get("input")
            if not isinstance(source, str) or READ_COMMAND.search(source) is None:
                continue
            for evidence in skills.values():
                if any(path_form in source for path_form in evidence["path_forms"]):
                    evidence["body_read_command_lines"].append(line_number)
    items: list[dict[str, Any]] = []
    for name, evidence in sorted(skills.items()):
        items.append(
            {
                "assistant_reference_lines": sorted(set(evidence["assistant_reference_lines"])),
                "body_read_command_lines": sorted(set(evidence["body_read_command_lines"])),
                "name": name,
                "path": evidence["path"],
            }
        )
    return {"schema_version": 1, "skills": items}


def main() -> int:
    """Parse inputs and emit the catalog-backed evidence report."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--transcript", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        report = resolve(arguments.catalog, arguments.transcript)
    except (OSError, UnicodeError, json.JSONDecodeError, ResolveError) as error:
        print(f"skill-use resolution failed: {error}", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
