#!/usr/bin/env python3
"""Audit review-oriented skill wording for implicit cross-effect authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Iterable


TRIGGER = re.compile(r"(?i)\b(review|audit|diagnos(?:e|is|tic)|inspect|analy[sz]e)\b")
BOUNDARY = re.compile(
    r"(?i)(?:explicit(?:ly)?\s+(?:asks?|requests?|authori[sz]es?)|only when (?:the )?user|separate authority|does not authorize|do not|must not|never|without .* authority)"
)
RULES: tuple[tuple[str, tuple[str, ...], re.Pattern[str]], ...] = (
    (
        "implicit-persistence",
        ("inline-analysis", "artifact-creation"),
        re.compile(r"(?i)(?:\b(?:write|save|persist)\b|create (?:a |the )?(?:report|ledger|artifact)|\.scratchpad)"),
    ),
    (
        "implicit-execution",
        ("inline-analysis", "collector-or-probe"),
        re.compile(r"(?i)(?:\b(?:run|execute|invoke|launch)\b.{0,50}\b(?:collector|probe|test|build|validat\w*|script|helper)\b)"),
    ),
    (
        "implicit-mutation",
        ("inline-analysis", "source-mutation"),
        re.compile(r"(?i)\b(?:fix|rewrite|apply|modify|edit|remediate)\b"),
    ),
    (
        "implicit-git",
        ("inline-analysis", "git-persistence"),
        re.compile(r"(?i)\b(?:stage|commit|amend|push)\b"),
    ),
    (
        "implicit-activation",
        ("creation-or-review", "activation-or-publication"),
        re.compile(r"(?i)\b(?:install|link|sync|synchronize|register|enable|hook|publish|deploy)\b"),
    ),
)
LINK = re.compile(r"\[[^\]]+\]\(([^)#?]+\.md)(?:#[^)]+)?\)")


def direct_markdown_files(package: Path) -> tuple[list[Path], list[str]]:
    skill = package / "SKILL.md"
    if not skill.is_file():
        return [], ["SKILL.md is missing"]
    files = [skill]
    errors: list[str] = []
    text = skill.read_text(encoding="utf-8")
    for target in sorted(set(LINK.findall(text))):
        candidate = (skill.parent / target).resolve()
        try:
            candidate.relative_to(package.resolve())
        except ValueError:
            errors.append(f"referenced Markdown escapes package: {target}")
            continue
        if not candidate.is_file():
            errors.append(f"referenced Markdown is missing: {target}")
            continue
        files.append(candidate)
    return files, errors


def scan_file(package: Path, path: Path) -> list[dict[str, object]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    findings: list[dict[str, object]] = []
    seen: set[tuple[int, str]] = set()
    for index, line in enumerate(lines):
        window = " ".join(lines[max(0, index - 1) : min(len(lines), index + 2)])
        if not TRIGGER.search(window) or BOUNDARY.search(window):
            continue
        for rule_id, effects, pattern in RULES:
            if not pattern.search(line):
                continue
            key = (index + 1, rule_id)
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                {
                    "path": path.resolve().relative_to(package.resolve()).as_posix(),
                    "line": index + 1,
                    "rule": rule_id,
                    "effect_classes": list(effects),
                    "severity": "advisory",
                    "excerpt": line.strip(),
                }
            )
    return findings


def audit(package: Path) -> tuple[int, dict[str, object]]:
    try:
        files, errors = direct_markdown_files(package)
    except (OSError, UnicodeDecodeError) as error:
        return 2, {"status": "error", "errors": [str(error)]}
    findings: list[dict[str, object]] = []
    hashes: dict[str, str] = {}
    for path in files:
        try:
            payload = path.read_bytes()
            hashes[path.resolve().relative_to(package.resolve()).as_posix()] = hashlib.sha256(payload).hexdigest()
            findings.extend(scan_file(package, path))
        except (OSError, UnicodeDecodeError) as error:
            errors.append(f"{path}: {error}")
    findings.sort(key=lambda item: (str(item["path"]), int(item["line"]), str(item["rule"])))
    report = {
        "schema_version": 1,
        "status": "error" if errors else ("findings" if findings else "clean"),
        "package": package.as_posix(),
        "files": hashes,
        "findings": findings,
        "errors": errors,
        "mutated_package": False,
    }
    if errors:
        return 2, report
    return (1 if findings else 0), report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--json", action="store_true", help="Output is always JSON; retained for explicit machine use.")
    args = parser.parse_args(argv)
    code, report = audit(args.package)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
