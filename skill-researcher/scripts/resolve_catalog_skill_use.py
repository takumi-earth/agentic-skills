#!/usr/bin/env python3
"""Report catalog-backed transcript leads without resolving or reading skill paths."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shlex
import sys
from typing import Any, Iterator


SKILL_REFERENCE = re.compile(r"(?<![\w$])\$([A-Za-z0-9][A-Za-z0-9:_-]*)")
PATH_START = r"(?<![^\s\"'`(<>=:,;\[{])"
PATH_END = r"(?![^\s\"'`),;:\]}])"


class ResolveError(Exception):
    """Describe malformed catalog or transcript input."""


def display_path(raw: str) -> str:
    """Preserve lexical identity, including relative paths and symlink aliases."""
    path = Path(raw).expanduser()
    try:
        relative = path.relative_to(Path.home())
    except ValueError:
        return str(path)
    return "~" if not relative.parts else f"~/{relative.as_posix()}"


def diagnostic(error: Exception) -> str:
    return str(error).replace(str(Path.home()), "~")


def string_leaves(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from string_leaves(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from string_leaves(item)


def message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return "\n".join(
        item["text"] for item in content
        if isinstance(item, dict)
        and isinstance(item.get("type"), str)
        and item.get("type") in {"text", "input_text", "output_text"}
        and isinstance(item.get("text"), str)
    )


def load_catalog(path: Path) -> list[dict[str, str]]:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    raw_skills = payload.get("skills") if isinstance(payload, dict) else None
    if not isinstance(raw_skills, list):
        raise ResolveError("catalog must contain a skills array")
    skills: set[tuple[str, str]] = set()
    for raw in raw_skills:
        if not isinstance(raw, dict):
            raise ResolveError("every catalog skill must be an object")
        name, body = raw.get("name"), raw.get("path")
        if not isinstance(name, str) or re.fullmatch(
            r"[a-z0-9][a-z0-9:-]{0,127}", name
        ) is None:
            raise ResolveError("catalog skill names must be lowercase skill identifiers")
        if not isinstance(body, str) or not body or Path(body).name != "SKILL.md":
            raise ResolveError("every catalog path must name a SKILL.md body")
        skills.add((name, display_path(body)))
    return [{"name": name, "path": path} for name, path in sorted(skills)]


def read_operands(command: str) -> tuple[str, list[str]]:
    """Recognize a small direct-read grammar; never evaluate shell or source code."""
    if any(char in command for char in ";|&><\n\r$`*?[]{}()"):
        return "", []
    try:
        words = shlex.split(command, comments=True)
    except ValueError:
        return "", []
    if not words:
        return "", []
    reader, args = Path(words[0]).name, words[1:]
    if reader == "sed":
        if args and args[0] in {"-n", "--quiet", "--silent"}:
            args = args[1:]
        if not args or re.fullmatch(r"(?:\d+(?:,\d+)?)?p", args[0]) is None:
            return "", []
        args = args[1:]
    elif reader in {"cat", "head", "tail"}:
        while args and args[0].startswith("-") and args[0] not in {"-", "--"}:
            option, args = args[0], args[1:]
            if reader == "cat":
                if re.fullmatch(r"-[AbeEnstTuv]+", option) is None:
                    return "", []
            elif option in {"-n", "-c", "--lines", "--bytes"}:
                if not args or re.fullmatch(r"[+-]?\d+", args[0]) is None:
                    return "", []
                args = args[1:]
            elif re.fullmatch(r"(?:-[nc]|--(?:lines|bytes)=)[+-]?\d+", option) is None:
                if option not in {"-q", "-v", "--quiet", "--silent", "--verbose"}:
                    return "", []
    else:
        return "", []
    if args and args[0] == "--":
        args = args[1:]
    elif any(arg.startswith("-") and arg != "-" for arg in args):
        return "", []
    return reader, [display_path(arg) for arg in args if arg != "-"]


def tool_input(payload: dict[str, Any]) -> tuple[str, str | None]:
    """Separate searchable input text from a supported direct shell command."""
    value = (
        payload.get("arguments")
        if payload["type"] == "function_call" else payload.get("input")
    )
    if payload["type"] == "function_call" and isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            pass
    name = str(payload.get("name", "")).rsplit(".", 1)[-1]
    command = None
    if name == "exec_command" and isinstance(value, dict) and isinstance(value.get("cmd"), str):
        command = value["cmd"]
    elif name == "exec" and payload["type"] == "custom_tool_call" and isinstance(value, str):
        command = value
    return "\n".join(string_leaves(value)), command


def resolve(catalog_path: Path, transcript_path: Path) -> dict[str, Any]:
    skills = load_catalog(catalog_path)
    names: dict[str, list[str]] = {}
    patterns: dict[str, re.Pattern[str]] = {}
    for skill in skills:
        path = skill["path"]
        names.setdefault(skill["name"], []).append(path)
        forms = {path, str(Path(path).expanduser())}
        if not Path(path).is_absolute() and not path.startswith("~"):
            forms.add("./" + path)
        alternatives = "|".join(re.escape(form) for form in sorted(forms))
        patterns[path] = re.compile(PATH_START + "(?:" + alternatives + ")" + PATH_END)
    references, mentions, candidates = [], [], []
    with transcript_path.expanduser().open(encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as error:
                raise ResolveError(f"malformed JSON at transcript line {line_number}: {error.msg}") from error
            if not isinstance(record, dict):
                raise ResolveError(f"transcript line {line_number} must be an object")
            if record.get("type") != "response_item":
                continue
            payload = record.get("payload")
            if not isinstance(payload, dict) or not isinstance(payload.get("type"), str):
                raise ResolveError(f"response_item at transcript line {line_number} needs a typed payload")
            kind = payload["type"]
            if kind == "message" and payload.get("role") == "assistant":
                tokens = set(SKILL_REFERENCE.findall(message_text(payload.get("content"))))
                for name in sorted(tokens & names.keys()):
                    references.append({
                        "line": line_number,
                        "name": name,
                        "candidate_paths": names[name],
                        "ambiguous": len(names[name]) > 1,
                    })
            if kind not in {"function_call", "custom_tool_call"}:
                continue
            if not isinstance(payload.get("name"), str):
                raise ResolveError(f"tool call at transcript line {line_number} needs a name")
            source, command = tool_input(payload)
            reader, operands = read_operands(command) if command is not None else ("", [])
            for skill in skills:
                event = {"line": line_number, "tool": payload.get("name"), **skill}
                if patterns[skill["path"]].search(source) or skill["path"] in operands:
                    mentions.append(event)
                if skill["path"] in operands:
                    candidates.append({**event, "reader": reader})
    return {
        "schema_version": 1,
        "catalog": skills,
        "assistant_references": references,
        "tool_path_mentions": mentions,
        "read_command_candidates": candidates,
        "evidence_limits": {
            "successful_reads_verified": False,
            "behavioral_use_evaluated": False,
            "current_topology_consulted": False,
            "unsupported_commands_are_path_mentions_only": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--transcript", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        report = resolve(arguments.catalog, arguments.transcript)
    except (OSError, UnicodeError, ValueError, RuntimeError, ResolveError) as error:
        print(f"skill-use resolution failed: {diagnostic(error)}", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
