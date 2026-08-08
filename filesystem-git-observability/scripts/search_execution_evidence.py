#!/usr/bin/env python3
"""Search bounded text records for named evidence markers.

The search is read-only outside its exclusive JSON report. It emits only
marker-local excerpts and hash-like tokens so unrelated conversation content
is not copied into the task artifact.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Iterable


ALLOWED_SUFFIXES = {".jsonl", ".json", ".log", ".txt", ".md"}
MAX_FILE_BYTES = 256 * 1024 * 1024
MAX_MATCHES_PER_FILE = 100
EXCERPT_RADIUS = 180

SHA256_PATTERN = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])")
CONTROL_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def candidate_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if not root.is_dir():
            continue
        for directory, names, filenames in os.walk(root):
            names.sort()
            filenames.sort()
            for filename in filenames:
                path = Path(directory) / filename
                try:
                    size = path.stat().st_size
                except OSError:
                    continue
                if (
                    path.suffix.lower() in ALLOWED_SUFFIXES
                    and 0 < size <= MAX_FILE_BYTES
                    and path.is_file()
                ):
                    yield path


def safe_excerpt(text: str, offset: int, marker: str) -> str:
    start = max(0, offset - EXCERPT_RADIUS)
    end = min(len(text), offset + len(marker) + EXCERPT_RADIUS)
    excerpt = text[start:end].replace("\n", "\\n").replace("\r", "\\r")
    return CONTROL_PATTERN.sub("?", excerpt)


def scan_file(path: Path, markers: dict[str, str]) -> dict[str, Any] | None:
    try:
        raw = path.read_bytes()
    except OSError as error:
        return {"path": str(path), "read_error": f"{type(error).__name__}: {error}"}
    text = raw.decode("utf-8", errors="replace")
    marker_counts: Counter[str] = Counter()
    matches: list[dict[str, Any]] = []
    for marker_name, marker in markers.items():
        offset = 0
        marker_match_count = 0
        while marker_match_count < MAX_MATCHES_PER_FILE:
            found = text.find(marker, offset)
            if found < 0:
                break
            marker_counts[marker_name] += 1
            marker_match_count += 1
            excerpt = safe_excerpt(text, found, marker)
            matches.append(
                {
                    "marker": marker_name,
                    "byte_offset_approx": len(text[:found].encode("utf-8")),
                    "excerpt": excerpt,
                    "sha256_tokens_in_excerpt": sorted(set(SHA256_PATTERN.findall(excerpt))),
                }
            )
            offset = found + len(marker)
    if not matches:
        return None
    return {
        "path": str(path),
        "size": len(raw),
        "file_sha256": hashlib.sha256(raw).hexdigest(),
        "marker_counts": dict(sorted(marker_counts.items())),
        "matches": matches,
        "truncated_markers": sorted(
            name for name, count in marker_counts.items() if count >= MAX_MATCHES_PER_FILE
        ),
    }


def atomic_create_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing report: {path}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, 0o600)
        os.link(temporary_path, path)
        temporary_path.unlink()
    finally:
        temporary_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, action="append", required=True)
    parser.add_argument("--marker", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--purpose", default="search durable execution evidence")
    arguments = parser.parse_args()

    markers: dict[str, str] = {}
    for value in arguments.marker:
        name, separator, marker = value.partition("=")
        if not separator or not name or not marker or name in markers:
            parser.error("each --marker must be a unique non-empty NAME=VALUE pair")
        markers[name] = marker
    roots = [path.expanduser().resolve() for path in arguments.root if path.is_dir()]
    if not roots:
        parser.error("none of the --root paths are directories")
    scanned = 0
    findings: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for path in candidate_files(roots):
        scanned += 1
        result = scan_file(path, markers)
        if result is None:
            continue
        if "read_error" in result:
            errors.append(result)
        else:
            findings.append(result)

    all_hashes = sorted(
        {
            token
            for finding in findings
            for match in finding["matches"]
            for token in match["sha256_tokens_in_excerpt"]
        }
    )
    report: dict[str, Any] = {
        "schema_version": 1,
        "purpose": arguments.purpose,
        "read_only_search": True,
        "markers": markers,
        "search_roots": [str(path) for path in roots],
        "candidate_files_scanned": scanned,
        "matching_files": findings,
        "read_errors": errors,
        "all_sha256_tokens_in_marker_local_excerpts": all_hashes,
    }
    atomic_create_json(arguments.output, report)
    summary = {
        "output": str(arguments.output),
        "search_roots": report["search_roots"],
        "candidate_files_scanned": scanned,
        "matching_file_count": len(findings),
        "read_error_count": len(errors),
        "sha256_token_count": len(all_hashes),
        "matching_paths": [finding["path"] for finding in findings],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
