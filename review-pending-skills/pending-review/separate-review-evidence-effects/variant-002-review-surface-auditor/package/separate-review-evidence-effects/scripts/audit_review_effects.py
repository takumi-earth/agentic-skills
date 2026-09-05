#!/usr/bin/env python3
"""Audit review-oriented skill wording for implicit cross-effect authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


TRIGGER = re.compile(r"(?i)\b(review|audit|diagnos(?:e|is|tic)|inspect|analy[sz]e)\b")
CREATION = re.compile(r"(?i)\b(?:create|creation|materialize|promote|promotion|adopt)\b")
NEGATION = re.compile(r"(?i)\b(?:do not|must not|never|does not authorize)\b")
REQUEST = re.compile(
    r"(?i)\b(?:only\s+)?(?:when|if)\s+(?:the\s+)?user\s+"
    r"(?:explicitly\s+)?(?:asks?|requests?|authori[sz]es?|approves?)\b"
    r"(?P<object>[^,;.!?]*)(?:[,;.!?]|$)"
)
ANALYSIS_OBJECT = re.compile(r"(?i)\b(?:review|audit|inspection|analysis|diagnosis)\s+(?:of|on|for)\b")
STATEMENT_END = re.compile(r"(?<=[.!?;])\s+|\n\s*\n|\s+but\s+|\n(?=\s*(?:#{1,6}\s|[-*+]\s|\d+[.)]\s))", re.IGNORECASE)
RULES: tuple[tuple[str, tuple[str, ...], re.Pattern[str]], ...] = (
    (
        "implicit-persistence",
        ("inline-analysis", "artifact-creation"),
        re.compile(r"(?i)(?:\b(?:write|save|persist)\b|create (?:a |the )?(?:report|ledger|artifact)|\.scratchpad)"),
    ),
    (
        "implicit-execution",
        ("inline-analysis", "collector-or-probe"),
        re.compile(r"(?is)(?:\b(?:run|execute|invoke|launch)\b.{0,50}\b(?:collector|probe|tests?|build|validat\w*|script|helper)\b)"),
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
REQUEST_OBJECTS = {
    "implicit-persistence": re.compile(r"(?i)\b(?:reports?|ledgers?|artifacts?|output|files?|writing|saving|persistence)\b"),
    "implicit-execution": re.compile(r"(?i)\b(?:collectors?|probes?|tests?|builds?|validation|verification|scripts?|helpers?)\b"),
    "implicit-mutation": re.compile(r"(?i)\b(?:fixes?|repairs?|rewrites?|changes?|edits?|remediation|implementation)\b"),
    "implicit-git": re.compile(r"(?i)\b(?:staging|stage|commits?|committing|amend|amending|push|pushing)\b"),
    "implicit-activation": re.compile(r"(?i)\b(?:install\w*|link\w*|sync\w*|regist\w*|enable\w*|publish\w*|publication|deploy\w*)\b"),
}
ACTION_REQUESTS = {
    "stage": r"stag(?:e|es|ing)",
    "commit": r"commit(?:s|ting)?",
    "amend": r"amend(?:s|ing|ment)?",
    "push": r"push(?:es|ing)?",
    "install": r"install(?:s|ing|ation)?",
    "link": r"link(?:s|ing)?",
    "sync": r"sync(?:s|ing|hroniz\w*)?",
    "synchronize": r"sync(?:s|ing|hroniz\w*)?",
    "register": r"regist(?:er\w*|ration)",
    "enable": r"enabl\w*",
    "publish": r"publish\w*|publication",
    "deploy": r"deploy\w*",
}


@dataclass(frozen=True)
class Source:
    name: str
    text: str
    sha256: str


def present(value: object) -> str:
    return re.sub(re.escape(str(Path.home())) + r"(?=/|$)", "~", str(value))


def direct_markdown_files(package: Path) -> tuple[list[Source], list[str]]:
    files: list[Source] = []
    errors: list[str] = []
    seen: set[Path] = set()

    def read_source(path: Path) -> Source | None:
        try:
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(package):
                raise ValueError(f"Markdown escapes package: {present(path)} -> {present(resolved)}")
            if not resolved.is_file():
                raise ValueError(f"Markdown is not a regular file: {present(path)}")
            if resolved in seen:
                return None
            seen.add(resolved)
            payload = resolved.read_bytes()
            source = Source(
                resolved.relative_to(package).as_posix(),
                payload.decode("utf-8"),
                hashlib.sha256(payload).hexdigest(),
            )
            files.append(source)
            return source
        except (OSError, UnicodeDecodeError, ValueError, RuntimeError) as error:
            errors.append(present(error))
            return None

    entry = read_source(package / "SKILL.md")
    if entry is None:
        return files, errors
    for target in sorted(set(LINK.findall(entry.text))):
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc:
            continue
        read_source(package / parsed.path)
    return files, errors


def has_effect_boundary(statement: str, match: re.Match[str], rule_id: str) -> bool:
    if NEGATION.search(statement[: match.start()]):
        return True
    for request in REQUEST.finditer(statement):
        subject = request.group("object").strip()
        if ANALYSIS_OBJECT.search(subject):
            continue
        action = match.group().lower()
        specific = ACTION_REQUESTS.get(action)
        object_matches = (
            re.search(rf"\b(?:{specific})\b", subject, re.IGNORECASE)
            if specific is not None
            else REQUEST_OBJECTS[rule_id].search(subject)
        )
        if object_matches:
            return True
        if request.start() > match.end() and re.fullmatch(r"(?i)(?:for\s+)?(?:it|one|this|that)", subject):
            return True
    return False


def scan_file(source: Source, review_context: bool, creation_context: bool) -> list[dict[str, object]]:
    lines = source.text.splitlines()
    findings: list[dict[str, object]] = []
    seen: set[tuple[int, str]] = set()
    start = 0
    spans: list[tuple[int, int]] = []
    for boundary in STATEMENT_END.finditer(source.text):
        spans.append((start, boundary.start()))
        start = boundary.end()
    spans.append((start, len(source.text)))
    for start, end in spans:
        statement = source.text[start:end]
        for rule_id, effects, pattern in RULES:
            if not review_context and not (creation_context and rule_id == "implicit-activation"):
                continue
            for match in pattern.finditer(statement):
                if has_effect_boundary(statement, match, rule_id):
                    continue
                line = source.text.count("\n", 0, start + match.start()) + 1
                key = (line, rule_id)
                if key in seen:
                    continue
                seen.add(key)
                findings.append(
                    {
                        "path": source.name,
                        "line": line,
                        "rule": rule_id,
                        "effect_classes": list(effects),
                        "severity": "advisory",
                        "excerpt": present(lines[line - 1].strip()),
                    }
                )
    return findings


def audit(package: Path) -> tuple[int, dict[str, object]]:
    files: list[Source] = []
    errors: list[str] = []
    try:
        package = package.expanduser().resolve(strict=True)
        if not package.is_dir():
            raise ValueError(f"Package is not a directory: {present(package)}")
        files, errors = direct_markdown_files(package)
    except (OSError, UnicodeDecodeError, ValueError, RuntimeError) as error:
        errors.append(present(error))
    findings: list[dict[str, object]] = []
    inherited_review = bool(files and TRIGGER.search(files[0].text))
    inherited_creation = bool(files and CREATION.search(files[0].text))
    for source in files:
        findings.extend(scan_file(source, inherited_review or bool(TRIGGER.search(source.text)), inherited_creation or bool(CREATION.search(source.text))))
    findings.sort(key=lambda item: (str(item["path"]), int(item["line"]), str(item["rule"])))
    report = {
        "schema_version": 1,
        "status": "error" if errors else ("findings" if findings else "clean"),
        "package": present(package),
        "files": {source.name: source.sha256 for source in files},
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
