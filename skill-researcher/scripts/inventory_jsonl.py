#!/usr/bin/env python3
"""Inventory Codex and Claude JSONL traces without copying trace bodies."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable


CORRECTION_PATTERNS = {
    "direct_rejection": re.compile(
        r"(?i)(?:^|\b)(?:no|nope|wrong|incorrect|stop|absolutely not)(?:\b|[,.!])"
    ),
    "prohibition": re.compile(
        r"(?i)\b(?:do not|don't|dont|never|must not|should not|shouldn't|cannot)\b"
    ),
    "behavior_correction": re.compile(
        r"(?i)\b(?:you (?:did|are|were|keep|ignored|missed|forgot|should|"
        r"shouldn't|need(?:ed)?|weren't|aren't)|why did you|i (?:said|asked|"
        r"told|meant)|not what i (?:said|asked|meant|wanted))\b"
    ),
    "redo_or_churn": re.compile(
        r"(?i)\b(?:restart|redo|rework|revert|undo|start over|try again|"
        r"do it again|still (?:wrong|not|doing)|keeps? (?:failing|changing))\b"
    ),
    "hard_boundary": re.compile(
        r"(?i)\b(?:staged|unstaged|verification|verify|commit|mutant|mutation|"
        r"subagents?|plan before|do not edit|don't edit|scope|boundary)\b"
    ),
}
INJECTED_BLOCK_RE = re.compile(
    r"(?is)<(?P<tag>system-reminder|local-command-caveat|local-command-stdout)>"
    r".*?</(?P=tag)>"
)
CONVERSATION_CATEGORIES = {"session", "project_session", "subagent_session"}


def sorted_counter(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def key_shape(value: Any) -> str:
    if isinstance(value, dict):
        return ",".join(sorted(str(key) for key in value))
    return f"<{type(value).__name__}>"


def scalar_kind(value: Any) -> str:
    if isinstance(value, str):
        return value if len(value) <= 120 else value[:117] + "..."
    if isinstance(value, dict):
        discriminator = value.get("type") or value.get("kind") or value.get("name")
        if isinstance(discriminator, str):
            return discriminator
        return "object:" + ",".join(sorted(str(key) for key in value))
    if value is None:
        return "<none>"
    return type(value).__name__


def timestamp_to_iso(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if not isinstance(value, (int, float)):
        return None
    seconds = float(value)
    if seconds > 10_000_000_000:
        seconds /= 1000
    try:
        return datetime.fromtimestamp(seconds, UTC).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def update_timestamp_bounds(
    current_min: str | None, current_max: str | None, value: Any
) -> tuple[str | None, str | None]:
    normalized = timestamp_to_iso(value)
    if normalized is None:
        return current_min, current_max
    if current_min is None or normalized < current_min:
        current_min = normalized
    if current_max is None or normalized > current_max:
        current_max = normalized
    return current_min, current_max


def extract_text_content(content: Any) -> list[str]:
    if isinstance(content, str):
        return [content]
    if not isinstance(content, list):
        return []
    texts: list[str] = []
    for block in content:
        if isinstance(block, str):
            texts.append(block)
        elif isinstance(block, dict) and block.get("type") in {
            "text",
            "input_text",
            "output_text",
        }:
            text = block.get("text")
            if isinstance(text, str):
                texts.append(text)
    return texts


def extract_user_texts(harness: str, record: dict[str, Any]) -> list[str]:
    if harness == "codex":
        record_type = record.get("type")
        payload = record.get("payload")
        if not isinstance(payload, dict):
            return []
        if (
            record_type == "response_item"
            and payload.get("type") == "message"
            and payload.get("role") == "user"
        ):
            return extract_text_content(payload.get("content"))
        if record_type == "event_msg" and payload.get("type") == "user_message":
            message = payload.get("message")
            return [message] if isinstance(message, str) else []
        return []

    if record.get("type") != "user" or record.get("isMeta") is True:
        return []
    message = record.get("message")
    if not isinstance(message, dict):
        return []
    return extract_text_content(message.get("content"))


def discover_files(roots: list[Path]) -> list[Path]:
    command = [
        "rg",
        "--files",
        "--hidden",
        "--no-ignore",
        "-0",
        *[str(root) for root in roots],
        "-g",
        "*.jsonl",
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True)
    except FileNotFoundError:
        return sorted(
            {path for root in roots for path in root.rglob("*.jsonl")},
            key=lambda path: str(path),
        )
    except subprocess.CalledProcessError as error:
        if error.returncode == 1:
            return []
        raise
    paths = [
        Path(raw.decode("utf-8", errors="surrogateescape"))
        for raw in result.stdout.split(b"\0")
        if raw
    ]
    return sorted(set(paths), key=lambda path: str(path))


def harness_for_path(path: Path) -> str:
    parts = path.parts
    if ".codex" in parts:
        return "codex"
    if ".claude" in parts:
        return "claude"
    return "unknown"


def classify_file(harness: str, path: Path) -> str:
    path_text = str(path)
    if harness == "codex":
        if path.name == "history.jsonl" and path.parent.name == ".codex":
            return "history"
        if path.name == "session_index.jsonl":
            return "session_index"
        if "/sessions/" in path_text or "/archived_sessions/" in path_text:
            return "session"
        if "/worktrees/" in path_text:
            return "repository_fixture"
        if "/plugins/" in path_text:
            return "plugin_fixture"
        return "other"

    if path.name == "history.jsonl" and path.parent.name == ".claude":
        return "history"
    if "/projects/" in path_text and "/subagents/" in path_text:
        return "subagent_session"
    if "/projects/" in path_text:
        return "project_session"
    if "/jobs/" in path_text:
        return "job_timeline"
    if "/plugins/" in path_text:
        return "plugin_log"
    return "other"


def relative_to_root(path: Path, roots: list[Path]) -> str:
    for root in roots:
        try:
            return str(path.relative_to(root))
        except ValueError:
            continue
    return path.name


@dataclass
class CorpusSchema:
    files: int = 0
    bytes: int = 0
    lines: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    categories: Counter[str] = field(default_factory=Counter)
    record_types: Counter[str] = field(default_factory=Counter)
    top_level_shapes: Counter[str] = field(default_factory=Counter)
    shapes_by_record_type: dict[str, Counter[str]] = field(
        default_factory=lambda: defaultdict(Counter)
    )
    payload_types: Counter[str] = field(default_factory=Counter)
    payload_shapes_by_type: dict[str, Counter[str]] = field(
        default_factory=lambda: defaultdict(Counter)
    )
    message_roles: Counter[str] = field(default_factory=Counter)
    message_shapes_by_role: dict[str, Counter[str]] = field(
        default_factory=lambda: defaultdict(Counter)
    )
    content_block_types: Counter[str] = field(default_factory=Counter)
    content_block_shapes_by_type: dict[str, Counter[str]] = field(
        default_factory=lambda: defaultdict(Counter)
    )
    tool_names: Counter[str] = field(default_factory=Counter)

    def as_dict(self) -> dict[str, Any]:
        return {
            "files": self.files,
            "bytes": self.bytes,
            "lines": self.lines,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "categories": sorted_counter(self.categories),
            "record_types": sorted_counter(self.record_types),
            "top_level_key_shapes": sorted_counter(self.top_level_shapes),
            "top_level_key_shapes_by_record_type": {
                key: sorted_counter(value)
                for key, value in sorted(self.shapes_by_record_type.items())
            },
            "payload_types": sorted_counter(self.payload_types),
            "payload_key_shapes_by_type": {
                key: sorted_counter(value)
                for key, value in sorted(self.payload_shapes_by_type.items())
            },
            "message_roles": sorted_counter(self.message_roles),
            "message_key_shapes_by_role": {
                key: sorted_counter(value)
                for key, value in sorted(self.message_shapes_by_role.items())
            },
            "content_block_types": sorted_counter(self.content_block_types),
            "content_block_key_shapes_by_type": {
                key: sorted_counter(value)
                for key, value in sorted(self.content_block_shapes_by_type.items())
            },
            "tool_names": sorted_counter(self.tool_names),
        }


def observe_content_blocks(schema: CorpusSchema, content: Any) -> None:
    if isinstance(content, str):
        schema.content_block_types["<string>"] += 1
        return
    if not isinstance(content, list):
        return
    for block in content:
        if not isinstance(block, dict):
            schema.content_block_types[f"<{type(block).__name__}>"] += 1
            continue
        block_type = str(block.get("type", "<missing>"))
        schema.content_block_types[block_type] += 1
        schema.content_block_shapes_by_type[block_type][key_shape(block)] += 1
        if block_type == "tool_use":
            name = block.get("name")
            if isinstance(name, str):
                schema.tool_names[name] += 1


def observe_schema(schema: CorpusSchema, record: dict[str, Any]) -> None:
    record_type = str(record.get("type", "<missing>"))
    top_shape = key_shape(record)
    schema.record_types[record_type] += 1
    schema.top_level_shapes[top_shape] += 1
    schema.shapes_by_record_type[record_type][top_shape] += 1

    payload = record.get("payload")
    if isinstance(payload, dict):
        payload_type = str(payload.get("type", "<missing>"))
        schema.payload_types[payload_type] += 1
        schema.payload_shapes_by_type[payload_type][key_shape(payload)] += 1
        if payload_type in {"function_call", "custom_tool_call"}:
            name = payload.get("name")
            if isinstance(name, str):
                schema.tool_names[name] += 1
        if payload_type == "message":
            role = str(payload.get("role", "<missing>"))
            schema.message_roles[role] += 1
            schema.message_shapes_by_role[role][key_shape(payload)] += 1
            observe_content_blocks(schema, payload.get("content"))

    message = record.get("message")
    if isinstance(message, dict):
        role = str(message.get("role", "<missing>"))
        schema.message_roles[role] += 1
        schema.message_shapes_by_role[role][key_shape(message)] += 1
        observe_content_blocks(schema, message.get("content"))


def inventory_file(
    path: Path,
    schema: CorpusSchema,
    roots: list[Path],
    domain_re: re.Pattern[str] | None,
) -> dict[str, Any]:
    harness = harness_for_path(path)
    category = classify_file(harness, path)
    stat = path.stat()
    record_types: Counter[str] = Counter()
    payload_types: Counter[str] = Counter()
    message_roles: Counter[str] = Counter()
    block_types: Counter[str] = Counter()
    tool_names: Counter[str] = Counter()
    top_shapes: Counter[str] = Counter()
    session_ids: set[str] = set()
    cwds: set[str] = set()
    agents: set[str] = set()
    sources: set[str] = set()
    models: set[str] = set()
    invalid_line_numbers: list[int] = []
    user_turn_line_numbers: set[int] = set()
    domain_line_numbers: set[int] = set()
    correction_line_numbers: set[int] = set()
    correction_signals: Counter[str] = Counter()
    user_text_hashes: set[str] = set()
    user_text_hash_order: list[str] = []
    user_message_count = 0
    user_text_bytes = 0
    domain_text_mentions = 0
    timestamp_min: str | None = None
    timestamp_max: str | None = None
    line_count = 0
    blank_lines = 0
    valid_records = 0

    with path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line_count = line_number
            if not raw_line.strip():
                blank_lines += 1
                continue
            try:
                record = json.loads(raw_line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                invalid_line_numbers.append(line_number)
                continue
            if not isinstance(record, dict):
                record_types[f"<{type(record).__name__}>"] += 1
                valid_records += 1
                continue

            valid_records += 1
            observe_schema(schema, record)
            record_type = str(record.get("type", "<missing>"))
            record_types[record_type] += 1
            top_shapes[key_shape(record)] += 1
            timestamp_min, timestamp_max = update_timestamp_bounds(
                timestamp_min, timestamp_max, record.get("timestamp")
            )
            timestamp_min, timestamp_max = update_timestamp_bounds(
                timestamp_min, timestamp_max, record.get("ts")
            )

            payload = record.get("payload")
            if isinstance(payload, dict):
                payload_type = str(payload.get("type", "<missing>"))
                payload_types[payload_type] += 1
                if record_type == "session_meta":
                    for key in ("id", "session_id"):
                        value = payload.get(key)
                        if isinstance(value, str):
                            session_ids.add(value)
                cwd = payload.get("cwd")
                if isinstance(cwd, str):
                    cwds.add(cwd)
                for key in ("source", "thread_source", "originator"):
                    if key in payload:
                        sources.add(f"{key}={scalar_kind(payload.get(key))}")
                for key in ("model", "model_provider"):
                    value = payload.get(key)
                    if isinstance(value, str):
                        models.add(value)
                timestamp_min, timestamp_max = update_timestamp_bounds(
                    timestamp_min, timestamp_max, payload.get("timestamp")
                )
                if payload_type in {"function_call", "custom_tool_call"}:
                    name = payload.get("name")
                    if isinstance(name, str):
                        tool_names[name] += 1

            for key in ("sessionId", "session_id"):
                value = record.get(key)
                if isinstance(value, str):
                    session_ids.add(value)
            cwd = record.get("cwd")
            if isinstance(cwd, str):
                cwds.add(cwd)
            agent_id = record.get("agentId")
            if isinstance(agent_id, str):
                agents.add(agent_id)
            for key in ("entrypoint", "userType"):
                if key in record:
                    sources.add(f"{key}={scalar_kind(record.get(key))}")

            message = record.get("message")
            if isinstance(message, dict):
                role = str(message.get("role", "<missing>"))
                message_roles[role] += 1
                model = message.get("model")
                if isinstance(model, str):
                    models.add(model)
                content = message.get("content")
                if isinstance(content, list):
                    for block in content:
                        if not isinstance(block, dict):
                            block_types[f"<{type(block).__name__}>"] += 1
                            continue
                        block_type = str(block.get("type", "<missing>"))
                        block_types[block_type] += 1
                        if block_type == "tool_use":
                            name = block.get("name")
                            if isinstance(name, str):
                                tool_names[name] += 1
                elif isinstance(content, str):
                    block_types["<string>"] += 1

            if isinstance(payload, dict) and payload.get("type") == "message":
                role = str(payload.get("role", "<missing>"))
                message_roles[role] += 1
                content = payload.get("content")
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict):
                            block_types[str(block.get("type", "<missing>"))] += 1
                elif isinstance(content, str):
                    block_types["<string>"] += 1

            for text in extract_user_texts(harness, record):
                cleaned = INJECTED_BLOCK_RE.sub(" ", text).strip()
                if not cleaned:
                    continue
                digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
                if digest in user_text_hashes:
                    continue
                user_text_hashes.add(digest)
                user_text_hash_order.append(digest)
                user_turn_line_numbers.add(line_number)
                user_message_count += 1
                user_text_bytes += len(cleaned.encode("utf-8"))
                if domain_re is not None:
                    matches = domain_re.findall(cleaned)
                    if matches:
                        domain_line_numbers.add(line_number)
                        domain_text_mentions += len(matches)
                matched_correction = False
                for signal, pattern in CORRECTION_PATTERNS.items():
                    matches = pattern.findall(cleaned)
                    if matches:
                        correction_signals[signal] += len(matches)
                        matched_correction = True
                if matched_correction:
                    correction_line_numbers.add(line_number)

    path_text = str(path)
    path_domain = bool(domain_re and domain_re.search(path_text))
    cwd_domain = bool(domain_re and any(domain_re.search(cwd) for cwd in cwds))
    domain_relevant = (
        category in CONVERSATION_CATEGORIES
        if domain_re is None
        else path_domain or cwd_domain or domain_text_mentions > 0
    )
    is_subagent = category == "subagent_session" or any(
        "thread_source=subagent" in source for source in sources
    )
    is_primary_conversation = (
        category in {"session", "project_session"} and not is_subagent
    )

    schema.files += 1
    schema.bytes += stat.st_size
    schema.lines += line_count
    schema.valid_records += valid_records
    schema.invalid_records += len(invalid_line_numbers)
    schema.categories[category] += 1

    return {
        "harness": harness,
        "category": category,
        "path": path_text,
        "relative_path": relative_to_root(path, roots),
        "size_bytes": stat.st_size,
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
        "line_count": line_count,
        "blank_line_count": blank_lines,
        "valid_record_count": valid_records,
        "invalid_record_count": len(invalid_line_numbers),
        "invalid_line_numbers": invalid_line_numbers,
        "timestamp_min": timestamp_min,
        "timestamp_max": timestamp_max,
        "record_type_counts": sorted_counter(record_types),
        "payload_type_counts": sorted_counter(payload_types),
        "message_role_counts": sorted_counter(message_roles),
        "content_block_type_counts": sorted_counter(block_types),
        "tool_name_counts": sorted_counter(tool_names),
        "top_level_key_shapes": sorted_counter(top_shapes),
        "session_ids": sorted(session_ids),
        "cwds": sorted(cwds),
        "agent_ids": sorted(agents),
        "sources": sorted(sources),
        "models": sorted(models),
        "is_primary_conversation": is_primary_conversation,
        "is_subagent": is_subagent,
        "domain_relevant": domain_relevant,
        "domain_path_signal": path_domain,
        "domain_cwd_signal": cwd_domain,
        "domain_text_mention_count": domain_text_mentions,
        "domain_line_numbers": sorted(domain_line_numbers),
        "user_message_count": user_message_count,
        "user_text_bytes": user_text_bytes,
        "user_turn_line_numbers": sorted(user_turn_line_numbers),
        "user_text_hash_prefix": user_text_hash_order[:8],
        "user_text_hash_suffix": user_text_hash_order[-8:],
        "correction_signal_counts": sorted_counter(correction_signals),
        "correction_signal_count": sum(correction_signals.values()),
        "correction_message_count": len(correction_line_numbers),
        "correction_line_numbers": sorted(correction_line_numbers),
    }


def write_ndjson(path: Path, records: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            json.dump(record, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")


def write_tsv(path: Path, records: list[dict[str, Any]]) -> None:
    fieldnames = [
        "harness",
        "category",
        "path",
        "size_bytes",
        "line_count",
        "valid_record_count",
        "invalid_record_count",
        "timestamp_min",
        "timestamp_max",
        "session_ids",
        "cwds",
        "is_primary_conversation",
        "is_subagent",
        "domain_relevant",
        "domain_cwd_signal",
        "domain_text_mention_count",
        "user_message_count",
        "correction_signal_count",
        "correction_message_count",
        "correction_line_numbers",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, dialect="excel-tab")
        writer.writeheader()
        for record in records:
            row = {key: record.get(key) for key in fieldnames}
            for key in ("session_ids", "cwds", "correction_line_numbers"):
                row[key] = json.dumps(row[key], ensure_ascii=False)
            writer.writerow(row)


def human_bytes(value: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    amount = float(value)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:.1f} {unit}"
        amount /= 1024
    raise AssertionError("unreachable")


def markdown_summary(
    records: list[dict[str, Any]],
    schemas: dict[str, CorpusSchema],
    generated_at: str,
    domain_regex: str | None,
) -> str:
    candidates = [
        record
        for record in records
        if record["domain_relevant"] and record["category"] in CONVERSATION_CATEGORIES
    ]
    correction_candidates = [
        record for record in candidates if record["correction_signal_count"] > 0
    ]
    lines = [
        "# JSONL trace inventory",
        "",
        f"Generated at `{generated_at}`.",
        "",
        "This inventory contains metadata, record/key shapes, identifiers, working",
        "directories, hashes, counts, and heuristic signal locations. It excludes raw",
        "message bodies, tool arguments, tool outputs, and pasted content.",
        "",
        "## Study selector",
        "",
        (
            f"- Domain regular expression: `{domain_regex}`"
            if domain_regex
            else "- Domain regular expression: none; all conversation traces are candidates."
        ),
        "",
        "## Corpus totals",
        "",
        f"- Files: `{len(records):,}`",
        f"- Bytes: `{sum(row['size_bytes'] for row in records):,}`",
        f"- JSONL lines: `{sum(row['line_count'] for row in records):,}`",
        f"- Candidate conversation traces: `{len(candidates):,}`",
        f"- Candidates with correction signals: `{len(correction_candidates):,}`",
        "",
        "| Harness | Files | Bytes | Lines | Valid records | Invalid records |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for harness in ("codex", "claude"):
        schema = schemas[harness]
        lines.append(
            f"| `{harness}` | {schema.files:,} | {schema.bytes:,} | "
            f"{schema.lines:,} | {schema.valid_records:,} | "
            f"{schema.invalid_records:,} |"
        )

    lines.extend(["", "## File categories", ""])
    for harness in ("codex", "claude"):
        lines.extend([f"### `{harness}`", ""])
        for category, count in sorted_counter(schemas[harness].categories).items():
            lines.append(f"- `{category}`: `{count:,}`")
        lines.append("")

    lines.extend(
        [
            "## Artifact map",
            "",
            "- `inventory.ndjson`: complete machine-readable row per source file.",
            "- `inventory.tsv`: compact row per source file.",
            "- `all-files.txt`: sorted absolute source path list.",
            "- `schema-summary.json`: aggregate record and nested key shapes.",
            "- `candidates.ndjson`: domain-relevant conversation traces.",
            "- `candidate-files.txt`: sorted candidate trace paths.",
            "",
            "Correction signals are triage heuristics, not conclusions. Inspect cited user",
            "turns in context and exclude injected instructions, copied history, worker",
            "packets, notifications, summaries, user self-corrections, and external churn.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a privacy-preserving Codex/Claude JSONL inventory."
    )
    parser.add_argument(
        "--root",
        action="append",
        dest="roots",
        type=Path,
        required=True,
        help="Authorized root to scan; repeat for multiple roots.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace known generated inventory artifacts in the output directory.",
    )
    parser.add_argument(
        "--domain-regex",
        help="Regex selecting candidate paths, CWDs, or visible user messages.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=100,
        help="Emit progress after this many files; use 0 to disable.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.progress_every < 0:
        raise SystemExit("--progress-every must be nonnegative")
    try:
        domain_re = (
            re.compile(args.domain_regex) if args.domain_regex is not None else None
        )
    except re.error as error:
        raise SystemExit(f"invalid --domain-regex: {error}") from error

    roots = [root.expanduser().resolve() for root in args.roots]
    missing = [root for root in roots if not root.is_dir()]
    if missing:
        raise SystemExit(
            "scan root is not a directory: " + ", ".join(str(path) for path in missing)
        )
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_names = (
        "inventory.ndjson",
        "inventory.tsv",
        "candidates.ndjson",
        "all-files.txt",
        "candidate-files.txt",
        "schema-summary.json",
        "inventory-summary.md",
    )
    existing_outputs = [
        output_dir / name for name in output_names if (output_dir / name).exists()
    ]
    if existing_outputs and not args.replace:
        rendered = ", ".join(str(path) for path in existing_outputs)
        raise SystemExit(
            "generated output already exists; choose a new directory or pass "
            f"--replace after authorization: {rendered}"
        )
    files = [
        path
        for path in discover_files(roots)
        if not path.resolve().is_relative_to(output_dir)
    ]
    schemas = {"codex": CorpusSchema(), "claude": CorpusSchema()}
    records: list[dict[str, Any]] = []
    total_bytes = sum(path.stat().st_size for path in files)
    processed_bytes = 0

    print(
        f"Discovered {len(files):,} JSONL files totaling {human_bytes(total_bytes)}.",
        file=sys.stderr,
        flush=True,
    )
    for index, path in enumerate(files, start=1):
        harness = harness_for_path(path)
        if harness not in schemas:
            continue
        record = inventory_file(path, schemas[harness], roots, domain_re)
        records.append(record)
        processed_bytes += record["size_bytes"]
        if args.progress_every and (
            index % args.progress_every == 0 or index == len(files)
        ):
            percent = (processed_bytes / total_bytes * 100) if total_bytes else 100
            print(
                f"Inventoried {index:,}/{len(files):,} files "
                f"({human_bytes(processed_bytes)}, {percent:.1f}% by bytes).",
                file=sys.stderr,
                flush=True,
            )

    records.sort(key=lambda record: record["path"])
    candidates = [
        record
        for record in records
        if record["domain_relevant"] and record["category"] in CONVERSATION_CATEGORIES
    ]
    generated_at = datetime.now(UTC).isoformat()
    schema_document = {
        "generated_at": generated_at,
        "roots": [str(root) for root in roots],
        "domain_regex": args.domain_regex,
        "privacy": {
            "message_bodies_included": False,
            "tool_arguments_included": False,
            "tool_outputs_included": False,
            "pasted_contents_included": False,
        },
        "harnesses": {harness: schema.as_dict() for harness, schema in schemas.items()},
    }

    write_ndjson(output_dir / "inventory.ndjson", records)
    write_tsv(output_dir / "inventory.tsv", records)
    write_ndjson(output_dir / "candidates.ndjson", candidates)
    with (output_dir / "all-files.txt").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record["path"] + "\n")
    with (output_dir / "candidate-files.txt").open("w", encoding="utf-8") as handle:
        for record in candidates:
            handle.write(record["path"] + "\n")
    with (output_dir / "schema-summary.json").open("w", encoding="utf-8") as handle:
        json.dump(schema_document, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    with (output_dir / "inventory-summary.md").open("w", encoding="utf-8") as handle:
        handle.write(
            markdown_summary(records, schemas, generated_at, args.domain_regex)
        )

    print(
        f"Wrote {len(records):,} inventory rows and {len(candidates):,} "
        f"candidates to {output_dir}.",
        file=sys.stderr,
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
