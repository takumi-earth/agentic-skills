#!/usr/bin/env python3
"""Inventory lexical signals of brittle source-transformation mechanisms."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
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
    raw = path.read_bytes()
    lines = raw.decode("utf-8").split("\n")
    source_hash = "sha256:" + hashlib.sha256(raw).hexdigest()
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
                "source_hash": source_hash,
            }
        )
    return sites


def iter_source_files(root: Path, excluded: list[Path]) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix in DEFAULT_SUFFIXES else []
    if not root.is_dir():
        raise ValueError(f"source root is not a file or directory: {root}")
    found = []
    def fail(error):
        raise error
    for base, directories, names in os.walk(root, followlinks=False, onerror=fail):
        for name in list(directories):
            path = Path(base) / name
            if name == '.git' or path.is_symlink():
                directories.remove(name)
                if path.is_symlink():
                    excluded.append(path)
        for name in names:
            path = Path(base) / name
            if path.is_symlink():
                excluded.append(path)
            elif path.suffix in DEFAULT_SUFFIXES:
                found.append(path)
    return sorted(found)


def select_root(repository: Path, root: Path) -> Path:
    expanded = root.expanduser()
    selected = Path(os.path.abspath(repository / expanded))
    if not selected.is_relative_to(repository):
        raise ValueError(f"root escapes repository: {root}")
    relative = selected.relative_to(repository)
    current = repository
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"selected root crosses a symlink: {root}")
    selected.stat()  # Missing or unreadable roots must not become empty success.
    return selected


def build_inventory(repository: Path, roots: list[Path]) -> dict[str, object]:
    resolved_repo = repository.expanduser().resolve(strict=True)
    if not resolved_repo.is_dir():
        raise ValueError("repository must be a directory")
    selected = sorted({select_root(resolved_repo, root) for root in roots})
    excluded = []
    paths = sorted({path for root in selected for path in iter_source_files(root, excluded)})
    sites = []
    for path in paths:
        if path.is_symlink():
            raise ValueError(f"source changed into a symlink: {path}")
        sites.extend(scan_file(path, path.relative_to(resolved_repo).as_posix()))
    return dict(schema_version=1, roots=[str(p.relative_to(resolved_repo)) for p in selected],
                status='complete', files_scanned=len(paths), line_model='LF', sites=sites,
                excluded_symlinks=sorted({str(p.relative_to(resolved_repo)) for p in excluded}))


def display(value: str) -> str:
    return re.sub(re.escape(str(Path.home())) + r"(?=$|[/\s\x27\x22:,)])", "~", value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--root", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        inventory = build_inventory(args.repo, args.root)
    except (OSError, ValueError, UnicodeError, RuntimeError) as error:
        print(json.dumps({"status": "error", "error": display(str(error))}, sort_keys=True))
        return 2
    rendered = json.dumps(inventory, indent=2, sort_keys=True) + "\n"
    if args.output:
        try:
            args.output.expanduser().write_text(rendered, encoding="utf-8")
        except OSError as error:
            print(json.dumps({"status": "error", "error": display(str(error))}))
            return 2
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
