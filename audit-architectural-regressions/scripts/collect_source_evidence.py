#!/usr/bin/env python3
"""Collect deterministic, line-anchored evidence from complete Git source blobs."""

from __future__ import annotations

import argparse
from bisect import bisect_right
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from typing import Any


SCHEMA_VERSION = 1


class EvidenceError(Exception):
    """Raised when a source-evidence specification or capture is invalid."""


def normalize_home(text: str) -> str:
    """Normalize the current home directory in serialized and human output."""
    home = str(Path.home().resolve())
    if text == home:
        return "~"
    return text.replace(home + os.sep, "~/")


def require_mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{label} must be an object")
    return value


def require_list(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise EvidenceError(f"{label} must be an array")
    return value


def require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise EvidenceError(f"{label} must be a non-empty string")
    return value


def require_nonnegative_int(value: object, label: str, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EvidenceError(f"{label} must be a non-negative integer")
    return value


def require_bool(value: object, label: str, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise EvidenceError(f"{label} must be a boolean")
    return value


def resolve_repository(raw_repository: str, spec_path: Path) -> Path:
    expanded = Path(os.path.expanduser(raw_repository))
    repository = expanded if expanded.is_absolute() else spec_path.parent / expanded
    repository = repository.resolve()
    if not repository.is_dir():
        raise EvidenceError(f"repository does not exist: {normalize_home(str(repository))}")
    return repository


def validate_relative_path(raw_path: str) -> str:
    path = PurePosixPath(raw_path)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise EvidenceError(f"source path must stay repository-relative: {raw_path}")
    return path.as_posix()


def run_git(repository: Path, arguments: list[str]) -> bytes:
    command = ["git", "-C", str(repository), *arguments]
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if completed.returncode != 0:
        stderr = normalize_home(completed.stderr.decode("utf-8", errors="replace").strip())
        rendered = " ".join(["git", "-C", normalize_home(str(repository)), *arguments])
        raise EvidenceError(f"command failed ({completed.returncode}): {rendered}: {stderr}")
    return completed.stdout


def resolve_checkpoint(repository: Path, checkpoint: dict[str, Any]) -> dict[str, str]:
    checkpoint_id = require_string(checkpoint.get("id"), "checkpoint.id")
    revision = require_string(checkpoint.get("revision"), f"checkpoint {checkpoint_id}.revision")
    if revision == "WORKTREE":
        resolved = run_git(repository, ["rev-parse", "--verify", "HEAD^{commit}"]).decode("utf-8").strip()
        return {
            "id": checkpoint_id,
            "revision": revision,
            "resolved_revision": resolved,
            "source_kind": "worktree",
            "repository": normalize_home(str(repository)),
        }
    resolved = run_git(repository, ["rev-parse", "--verify", f"{revision}^{{commit}}"]).decode("utf-8").strip()
    return {
        "id": checkpoint_id,
        "revision": revision,
        "resolved_revision": resolved,
        "source_kind": "commit",
        "repository": normalize_home(str(repository)),
    }


def load_source(repository: Path, checkpoint: dict[str, str], relative_path: str) -> bytes:
    if checkpoint["source_kind"] == "commit":
        return run_git(repository, ["show", f"{checkpoint['resolved_revision']}:{relative_path}"])
    candidate = (repository / relative_path).resolve()
    try:
        candidate.relative_to(repository)
    except ValueError as error:
        raise EvidenceError(f"worktree source escapes repository: {relative_path}") from error
    try:
        return candidate.read_bytes()
    except OSError as error:
        raise EvidenceError(f"failed to read worktree source {relative_path}: {error}") from error


def compile_patterns(raw_patterns: object, query_id: str) -> list[re.Pattern[str]]:
    patterns = require_list(raw_patterns, f"query {query_id}.patterns")
    if not patterns:
        raise EvidenceError(f"query {query_id}.patterns must not be empty")
    compiled: list[re.Pattern[str]] = []
    for index, raw_pattern in enumerate(patterns):
        pattern = require_string(raw_pattern, f"query {query_id}.patterns[{index}]")
        try:
            compiled.append(re.compile(pattern, re.MULTILINE))
        except re.error as error:
            raise EvidenceError(f"query {query_id} has invalid pattern {pattern!r}: {error}") from error
    return compiled


def compile_optional_pattern(value: object, label: str) -> re.Pattern[str] | None:
    if value is None:
        return None
    pattern = require_string(value, label)
    try:
        return re.compile(pattern, re.MULTILINE)
    except re.error as error:
        raise EvidenceError(f"{label} has invalid pattern {pattern!r}: {error}") from error


def scoped_source(source: str, query: dict[str, Any], query_id: str) -> tuple[str, int, dict[str, Any] | None]:
    start_pattern = compile_optional_pattern(query.get("scope_start_pattern"), f"query {query_id}.scope_start_pattern")
    end_pattern = compile_optional_pattern(query.get("scope_end_pattern"), f"query {query_id}.scope_end_pattern")
    if start_pattern is None and end_pattern is None:
        return source, 0, None
    start_offset = 0
    if start_pattern is not None:
        start_match = start_pattern.search(source)
        if start_match is None:
            raise EvidenceError(f"query {query_id}.scope_start_pattern matched no source")
        start_offset = start_match.start()
    end_offset = len(source)
    if end_pattern is not None:
        end_match = end_pattern.search(source, start_offset)
        if end_match is None:
            raise EvidenceError(f"query {query_id}.scope_end_pattern matched no source")
        end_offset = end_match.start()
    if end_offset < start_offset:
        raise EvidenceError(f"query {query_id} scope ends before it starts")
    line_offset = source.count("\n", 0, start_offset)
    return (
        source[start_offset:end_offset],
        line_offset,
        {
            "start_pattern": normalize_home(start_pattern.pattern) if start_pattern is not None else None,
            "end_pattern": normalize_home(end_pattern.pattern) if end_pattern is not None else None,
            "line_start": line_offset + 1,
            "line_end": source.count("\n", 0, end_offset) + 1,
        },
    )


def merged_ranges(matches: list[tuple[int, int]], line_count: int, before: int, after: int) -> list[tuple[int, int]]:
    ranges = [(max(0, start - before), min(line_count, end + after)) for start, end in matches]
    merged: list[tuple[int, int]] = []
    for start, end in ranges:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def normalized_groups(match: re.Match[str]) -> dict[str, str | None]:
    named = match.groupdict()
    if named:
        return {name: normalize_home(value) if value is not None else None for name, value in named.items()}
    return {
        str(index): normalize_home(value) if value is not None else None
        for index, value in enumerate(match.groups(), start=1)
    }


def line_matches(lines: list[str], patterns: list[re.Pattern[str]]) -> tuple[list[tuple[int, int]], list[dict[str, Any]]]:
    spans: list[tuple[int, int]] = []
    captures: list[dict[str, Any]] = []
    for line_index, line in enumerate(lines):
        matching_patterns: list[int] = []
        for pattern_index, pattern in enumerate(patterns):
            match = pattern.search(line)
            if match is not None:
                matching_patterns.append(pattern_index)
                captures.append(
                    {
                        "pattern_index": pattern_index,
                        "line_start": line_index + 1,
                        "line_end": line_index + 1,
                        "groups": normalized_groups(match),
                    }
                )
        if matching_patterns:
            spans.append((line_index, line_index + 1))
    return spans, captures


def source_matches(source: str, patterns: list[re.Pattern[str]]) -> tuple[list[tuple[int, int]], list[dict[str, Any]]]:
    line_starts = [0]
    line_starts.extend(match.end() for match in re.finditer("\n", source))
    records: list[tuple[int, int, int, re.Match[str]]] = []
    for pattern_index, pattern in enumerate(patterns):
        for match in pattern.finditer(source):
            start_line = max(0, bisect_right(line_starts, match.start()) - 1)
            final_offset = match.start() if match.end() == match.start() else match.end() - 1
            end_line = max(start_line, bisect_right(line_starts, final_offset) - 1) + 1
            records.append((start_line, end_line, pattern_index, match))
    records.sort(key=lambda record: (record[0], record[1], record[2], record[3].start()))
    spans = [(start, end) for start, end, _pattern_index, _match in records]
    captures = [
        {
            "pattern_index": pattern_index,
            "line_start": start + 1,
            "line_end": end,
            "groups": normalized_groups(match),
        }
        for start, end, pattern_index, match in records
    ]
    return spans, captures


def capture_query(checkpoints: dict[str, tuple[dict[str, str], Path]], raw_query: object) -> dict[str, Any]:
    query = require_mapping(raw_query, "query")
    query_id = require_string(query.get("id"), "query.id")
    checkpoint_id = require_string(query.get("checkpoint"), f"query {query_id}.checkpoint")
    checkpoint_entry = checkpoints.get(checkpoint_id)
    if checkpoint_entry is None:
        raise EvidenceError(f"query {query_id} names unknown checkpoint {checkpoint_id}")
    checkpoint, repository = checkpoint_entry
    relative_path = validate_relative_path(require_string(query.get("path"), f"query {query_id}.path"))
    before = require_nonnegative_int(query.get("context_before"), f"query {query_id}.context_before", 2)
    after = require_nonnegative_int(query.get("context_after"), f"query {query_id}.context_after", 2)
    required = require_bool(query.get("required"), f"query {query_id}.required", True)
    match_mode = query.get("match_mode", "line")
    if match_mode not in ("line", "source"):
        raise EvidenceError(f"query {query_id}.match_mode must be 'line' or 'source'")
    patterns = compile_patterns(query.get("patterns"), query_id)
    source_bytes = load_source(repository, checkpoint, relative_path)
    try:
        source = source_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise EvidenceError(f"query {query_id} source is not UTF-8: {relative_path}") from error
    lines = source.splitlines()
    selected_source, line_offset, scope = scoped_source(source, query, query_id)
    selected_lines = selected_source.splitlines()
    matches, captures = line_matches(selected_lines, patterns) if match_mode == "line" else source_matches(selected_source, patterns)
    if line_offset:
        matches = [(start + line_offset, end + line_offset) for start, end in matches]
        captures = [
            {
                **capture,
                "line_start": capture["line_start"] + line_offset,
                "line_end": capture["line_end"] + line_offset,
            }
            for capture in captures
        ]
    if required and not matches:
        raise EvidenceError(f"required query {query_id} matched no lines in {checkpoint_id}:{relative_path}")
    snippets: list[dict[str, Any]] = []
    for start, end in merged_ranges(matches, len(lines), before, after):
        matched_lines = sorted(
            {
                line_number
                for match_start, match_end in matches
                if start <= match_start and match_end <= end
                for line_number in range(match_start + 1, match_end + 1)
            }
        )
        snippets.append(
            {
                "line_start": start + 1,
                "line_end": end,
                "matched_lines": matched_lines,
                "lines": [
                    {"number": index + 1, "text": normalize_home(lines[index])}
                    for index in range(start, end)
                ],
            }
        )
    return {
        "id": query_id,
        "checkpoint": checkpoint_id,
        "revision": checkpoint["revision"],
        "resolved_revision": checkpoint["resolved_revision"],
        "source_kind": checkpoint["source_kind"],
        "repository": checkpoint["repository"],
        "path": relative_path,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "patterns": [normalize_home(pattern.pattern) for pattern in patterns],
        "match_mode": match_mode,
        "required": required,
        "match_count": len(matches),
        "captures": captures,
        "snippets": snippets,
        "scope": scope,
    }


def longest_backtick_run(lines: list[dict[str, Any]]) -> int:
    longest = 0
    for line in lines:
        for match in re.finditer(r"`+", line["text"]):
            longest = max(longest, len(match.group(0)))
    return longest


def render_markdown(evidence: dict[str, Any]) -> str:
    output = [
        "# Source-first architectural evidence",
        "",
        "This appendix was generated from complete worktree files or complete Git blobs at resolved checkpoints. It does not use a Git diff as the classification model.",
        "",
        f"Repository: `{evidence['repository']}`",
    ]
    for query in evidence["queries"]:
        output.extend(
            [
                "",
                f"## `{query['id']}`",
                "",
                f"- Checkpoint: `{query['checkpoint']}` (`{query['revision']}` -> `{query['resolved_revision']}`)",
                f"- Repository: `{query['repository']}`",
                f"- Source: `{query['path']}`",
                f"- Source SHA-256: `{query['source_sha256']}`",
                f"- Matches: `{query['match_count']}`",
            ]
        )
        if query["scope"] is not None:
            output.append(f"- Scope: lines `{query['scope']['line_start']}-{query['scope']['line_end']}`")
        if not query["snippets"]:
            output.extend(["", "No source lines matched this optional query."])
            continue
        for snippet in query["snippets"]:
            locator = f"{query['checkpoint']}:{query['path']}:{snippet['line_start']}-{snippet['line_end']}"
            fence = "`" * max(3, longest_backtick_run(snippet["lines"]) + 1)
            width = len(str(snippet["line_end"]))
            output.extend(["", f"### `{locator}`", "", fence + "text"])
            output.extend(f"{line['number']:>{width}} | {line['text']}" for line in snippet["lines"])
            output.append(fence)
    return "\n".join(output) + "\n"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def collect(spec_path: Path) -> dict[str, Any]:
    try:
        raw_spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise EvidenceError(f"failed to read source-evidence specification: {error}") from error
    spec = require_mapping(raw_spec, "specification")
    if spec.get("schema_version") != SCHEMA_VERSION:
        raise EvidenceError(f"specification schema_version must be {SCHEMA_VERSION}")
    repository = resolve_repository(require_string(spec.get("repository"), "repository"), spec_path)
    raw_checkpoints = require_list(spec.get("checkpoints"), "checkpoints")
    if not raw_checkpoints:
        raise EvidenceError("checkpoints must not be empty")
    resolved_checkpoints: list[dict[str, str]] = []
    checkpoint_by_id: dict[str, tuple[dict[str, str], Path]] = {}
    for raw_checkpoint in raw_checkpoints:
        checkpoint_input = require_mapping(raw_checkpoint, "checkpoint")
        raw_checkpoint_repository = checkpoint_input.get("repository")
        checkpoint_repository = (
            repository
            if raw_checkpoint_repository is None
            else resolve_repository(require_string(raw_checkpoint_repository, f"checkpoint {checkpoint_input.get('id')}.repository"), spec_path)
        )
        checkpoint = resolve_checkpoint(checkpoint_repository, checkpoint_input)
        if checkpoint["id"] in checkpoint_by_id:
            raise EvidenceError(f"duplicate checkpoint id: {checkpoint['id']}")
        resolved_checkpoints.append(checkpoint)
        checkpoint_by_id[checkpoint["id"]] = (checkpoint, checkpoint_repository)
    raw_queries = require_list(spec.get("queries"), "queries")
    if not raw_queries:
        raise EvidenceError("queries must not be empty")
    queries: list[dict[str, Any]] = []
    query_ids: set[str] = set()
    for raw_query in raw_queries:
        captured = capture_query(checkpoint_by_id, raw_query)
        if captured["id"] in query_ids:
            raise EvidenceError(f"duplicate query id: {captured['id']}")
        query_ids.add(captured["id"])
        queries.append(captured)
    return {
        "schema_version": SCHEMA_VERSION,
        "repository": normalize_home(str(repository)),
        "checkpoints": resolved_checkpoints,
        "queries": queries,
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-markdown", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        evidence = collect(arguments.spec.resolve())
        json_output = json.dumps(evidence, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        atomic_write(arguments.output_json.resolve(), json_output)
        atomic_write(arguments.output_markdown.resolve(), render_markdown(evidence))
    except (EvidenceError, OSError) as error:
        print(f"error: {normalize_home(str(error))}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
