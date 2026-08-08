#!/usr/bin/env python3
"""Analyze one JSONL rollout for named runtime evidence markers.

Only records carrying task-specific execution markers are retained. The script
does not copy complete conversation turns or unrelated record payloads.
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


SHA256_PATTERN = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])")
CONTROL_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MAX_EXCERPT = 700

def strings(value: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from strings(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from strings(child, f"{path}[{index}]")


def safe_excerpt(value: str, marker: str) -> str:
    offset = value.find(marker)
    if offset < 0:
        return ""
    radius = MAX_EXCERPT // 2
    excerpt = value[max(0, offset - radius) : offset + len(marker) + radius]
    excerpt = excerpt.replace("\r", "\\r").replace("\n", "\\n")
    return CONTROL_PATTERN.sub("?", excerpt)


def record_kind(record: dict[str, Any]) -> dict[str, Any]:
    payload = record.get("payload")
    return {
        "record_type": record.get("type"),
        "payload_type": payload.get("type") if isinstance(payload, dict) else None,
        "role": payload.get("role") if isinstance(payload, dict) else None,
        "name": payload.get("name") if isinstance(payload, dict) else None,
        "call_id": payload.get("call_id") if isinstance(payload, dict) else None,
    }


def atomic_create(path: Path, value: dict[str, Any]) -> None:
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
    parser.add_argument("--rollout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--marker", action="append", required=True)
    parser.add_argument("--internal-marker", action="append", default=[])
    parser.add_argument("--cutoff")
    arguments = parser.parse_args()

    markers: dict[str, str] = {}
    for value in arguments.marker:
        name, separator, marker = value.partition("=")
        if not separator or not name or not marker or name in markers:
            parser.error("each --marker must be a unique non-empty NAME=VALUE pair")
        markers[name] = marker
    unknown_internal = sorted(set(arguments.internal_marker) - set(markers))
    if unknown_internal:
        parser.error(f"--internal-marker names are undefined: {unknown_internal}")

    raw = arguments.rollout.read_bytes()
    records_examined = 0
    malformed_lines: list[int] = []
    matches: list[dict[str, Any]] = []
    runtime_output_hashes: set[str] = set()
    runtime_marker_counts: Counter[str] = Counter()
    pre_failure_runtime_strings = 0

    for line_number, raw_line in enumerate(raw.splitlines(), start=1):
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError:
            malformed_lines.append(line_number)
            continue
        records_examined += 1
        if not isinstance(record, dict):
            continue
        timestamp = str(record.get("timestamp", ""))
        kind = record_kind(record)
        is_runtime_output = kind["payload_type"] in {
            "function_call_output",
            "custom_tool_call_output",
        }
        before_or_at_cutoff = (
            arguments.cutoff is None or not timestamp or timestamp <= arguments.cutoff
        )
        for value_path, value in strings(record):
            present = [name for name, marker in markers.items() if marker in value]
            if not present:
                continue
            if is_runtime_output and before_or_at_cutoff:
                pre_failure_runtime_strings += 1
                runtime_marker_counts.update(present)
                runtime_output_hashes.update(SHA256_PATTERN.findall(value))
            primary = present[0]
            matches.append(
                {
                    "line": line_number,
                    "timestamp": timestamp or None,
                    **kind,
                    "value_path": value_path,
                    "markers": present,
                    "runtime_output": is_runtime_output,
                    "before_or_at_cutoff": before_or_at_cutoff,
                    "sha256_tokens": sorted(set(SHA256_PATTERN.findall(value))),
                    "excerpt": safe_excerpt(value, markers[primary]),
                }
            )

    bounded_runtime_matches = [
        match
        for match in matches
        if match["runtime_output"] and match["before_or_at_cutoff"]
    ]
    serialized_internal_state_markers = sorted(
        {
            marker
            for match in bounded_runtime_matches
            for marker in match["markers"]
            if marker in arguments.internal_marker
        }
    )
    report: dict[str, Any] = {
        "schema_version": 1,
        "rollout": str(arguments.rollout),
        "rollout_sha256": hashlib.sha256(raw).hexdigest(),
        "records_examined": records_examined,
        "malformed_line_numbers": malformed_lines,
        "cutoff": arguments.cutoff,
        "markers": markers,
        "internal_marker_names": arguments.internal_marker,
        "task_marker_match_count": len(matches),
        "bounded_runtime_output_match_count": len(bounded_runtime_matches),
        "bounded_runtime_string_count": pre_failure_runtime_strings,
        "bounded_runtime_marker_counts": dict(sorted(runtime_marker_counts.items())),
        "bounded_runtime_sha256_tokens": sorted(runtime_output_hashes),
        "serialized_internal_state_markers": serialized_internal_state_markers,
        "matches": matches,
        "conclusion": {
            "sha256_token_observed_in_bounded_runtime_output": bool(runtime_output_hashes),
            "observed_internal_markers": serialized_internal_state_markers,
            "missing_internal_markers": sorted(
                set(arguments.internal_marker) - set(serialized_internal_state_markers)
            ),
        },
    }
    atomic_create(arguments.output, report)
    summary = {
        "output": str(arguments.output),
        "records_examined": records_examined,
        "malformed_line_count": len(malformed_lines),
        "task_marker_match_count": len(matches),
        "bounded_runtime_marker_counts": report[
            "bounded_runtime_marker_counts"
        ],
        "bounded_runtime_sha256_tokens": report[
            "bounded_runtime_sha256_tokens"
        ],
        "serialized_internal_state_markers": serialized_internal_state_markers,
        "conclusion": report["conclusion"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
