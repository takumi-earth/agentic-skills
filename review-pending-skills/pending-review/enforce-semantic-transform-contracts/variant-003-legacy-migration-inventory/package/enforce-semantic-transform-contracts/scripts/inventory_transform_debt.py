#!/usr/bin/env python3
"""Inventory lexical signals of brittle source-transformation mechanisms."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


SIGNALS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("fixed-path", re.compile(r"(?:\.join|Path(?:Buf)?::from|Path)\s*\(\s*[\"'][^\"']+\.(?:rs|ts|js|py)[\"']")),
    ("marker-gate", re.compile(r"(?i)(?:marker.*(?:contains|find|starts_with)|(?:contains|find|starts_with).*marker)")),
    ("whole-body", re.compile(r"(?i)(?:ReplaceWholeItem|whole[_-]?(?:item|body)|complete[_-]?(?:item|body)|pre[_-]?body|post[_-]?body)")),
    ("fingerprint", re.compile(r"(?i)(?:fingerprint|token[_-]?(?:signature|snapshot))")),
    ("hash", re.compile(r"(?i)(?:sha[-_]?256|source[_-]?hash|body[_-]?hash)")),
    ("regex-target", re.compile(r"(?:Regex::new|re\.compile|new\s+RegExp)\s*\(")),
    ("text-fallback", re.compile(r"(?i)(?:text|string|source).{0,24}(?:replace|fallback)|(?:replace|fallback).{0,24}(?:text|string|source)")),
)
DEFAULT_SUFFIXES = {".rs", ".py", ".ts", ".tsx", ".js", ".jsx"}


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def scan_file(path: Path, display_path: str) -> list[dict[str, object]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    sites: list[dict[str, object]] = []
    for line_number, line in enumerate(lines, start=1):
        matches = sorted(name for name, pattern in SIGNALS if pattern.search(line))
        if not matches:
            continue
        site_key = f"{display_path}:{line_number}:{'+'.join(matches)}"
        sites.append(
            {
                "site_key": site_key,
                "path": display_path,
                "line": line_number,
                "signals": matches,
                "owner": "unassigned",
                "disposition": "review",
                "review_state": "signal-only",
                "excerpt_hash": sha256_text(line.strip()),
            }
        )
    return sites


def iter_source_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix in DEFAULT_SUFFIXES else []
    if not root.is_dir():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix in DEFAULT_SUFFIXES and ".git" not in path.parts
    )


def build_inventory(repository: Path, roots: list[Path]) -> dict[str, object]:
    resolved_repo = repository.resolve()
    root_labels: list[str] = []
    sites: list[dict[str, object]] = []
    for root in roots:
        resolved_root = (resolved_repo / root).resolve() if not root.is_absolute() else root.resolve()
        try:
            relative_root = resolved_root.relative_to(resolved_repo).as_posix()
        except ValueError as error:
            raise ValueError(f"root escapes repository: {root}") from error
        root_labels.append(relative_root or ".")
        for path in iter_source_files(resolved_root):
            display = path.resolve().relative_to(resolved_repo).as_posix()
            sites.extend(scan_file(path, display))
    sites.sort(key=lambda item: (str(item["path"]), int(item["line"]), str(item["site_key"])))
    return {"schema_version": 1, "roots": sorted(set(root_labels)), "sites": sites}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--root", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        inventory = build_inventory(args.repo, args.root)
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "error", "error": str(error)}, sort_keys=True))
        return 2
    rendered = json.dumps(inventory, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
