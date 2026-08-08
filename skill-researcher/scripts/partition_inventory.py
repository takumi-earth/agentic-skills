#!/usr/bin/env python3
"""Group trace families and balance them across deterministic partitions."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Family:
    harness: str
    family_id: str
    records: list[dict[str, Any]] = field(default_factory=list)

    @property
    def size_bytes(self) -> int:
        return sum(int(record.get("size_bytes", 0)) for record in self.records)

    @property
    def line_count(self) -> int:
        return sum(int(record.get("line_count", 0)) for record in self.records)

    @property
    def user_messages(self) -> int:
        return sum(int(record.get("user_message_count", 0)) for record in self.records)

    @property
    def correction_messages(self) -> int:
        return sum(
            int(record.get("correction_message_count", 0)) for record in self.records
        )

    @property
    def primary_files(self) -> int:
        return sum(
            bool(record.get("is_primary_conversation")) for record in self.records
        )

    @property
    def subagent_files(self) -> int:
        return sum(bool(record.get("is_subagent")) for record in self.records)

    @property
    def core_domain(self) -> bool:
        return any(
            record.get("domain_cwd_signal") or record.get("domain_path_signal")
            for record in self.records
        )

    @property
    def timestamp_min(self) -> str | None:
        values = [
            str(record["timestamp_min"])
            for record in self.records
            if record.get("timestamp_min")
        ]
        return min(values) if values else None

    @property
    def timestamp_max(self) -> str | None:
        values = [
            str(record["timestamp_max"])
            for record in self.records
            if record.get("timestamp_max")
        ]
        return max(values) if values else None

    @property
    def cost(self) -> int:
        return (
            self.size_bytes
            + self.user_messages * 250_000
            + self.correction_messages * 500_000
        )

    def as_dict(self) -> dict[str, Any]:
        cwds: set[str] = set()
        session_ids: set[str] = set()
        paths: list[dict[str, Any]] = []
        for record in sorted(self.records, key=lambda item: str(item.get("path", ""))):
            cwds.update(str(value) for value in record.get("cwds", []))
            session_ids.update(str(value) for value in record.get("session_ids", []))
            paths.append(
                {
                    "path": record.get("path"),
                    "category": record.get("category"),
                    "size_bytes": record.get("size_bytes", 0),
                    "line_count": record.get("line_count", 0),
                    "timestamp_min": record.get("timestamp_min"),
                    "timestamp_max": record.get("timestamp_max"),
                    "is_primary_conversation": bool(
                        record.get("is_primary_conversation")
                    ),
                    "is_subagent": bool(record.get("is_subagent")),
                    "user_message_count": record.get("user_message_count", 0),
                    "user_turn_line_numbers": record.get("user_turn_line_numbers", []),
                    "domain_line_numbers": record.get("domain_line_numbers", []),
                    "correction_message_count": record.get(
                        "correction_message_count", 0
                    ),
                    "correction_line_numbers": record.get(
                        "correction_line_numbers", []
                    ),
                    "user_text_hash_prefix": record.get("user_text_hash_prefix", []),
                    "user_text_hash_suffix": record.get("user_text_hash_suffix", []),
                }
            )
        return {
            "harness": self.harness,
            "family_id": self.family_id,
            "focus_tier": "domain-cwd-or-path" if self.core_domain else "text-only",
            "file_count": len(self.records),
            "primary_file_count": self.primary_files,
            "subagent_file_count": self.subagent_files,
            "size_bytes": self.size_bytes,
            "line_count": self.line_count,
            "user_message_count": self.user_messages,
            "correction_message_count": self.correction_messages,
            "timestamp_min": self.timestamp_min,
            "timestamp_max": self.timestamp_max,
            "cwds": sorted(cwds),
            "session_ids": sorted(session_ids),
            "files": paths,
        }


@dataclass
class Partition:
    index: int
    families: list[Family] = field(default_factory=list)
    cost: int = 0

    def add(self, family: Family) -> None:
        self.families.append(family)
        self.cost += family.cost

    def summary(self) -> dict[str, Any]:
        return {
            "partition": self.index,
            "families": len(self.families),
            "files": sum(len(family.records) for family in self.families),
            "primary_files": sum(family.primary_files for family in self.families),
            "subagent_files": sum(family.subagent_files for family in self.families),
            "bytes": sum(family.size_bytes for family in self.families),
            "lines": sum(family.line_count for family in self.families),
            "user_messages": sum(family.user_messages for family in self.families),
            "correction_messages": sum(
                family.correction_messages for family in self.families
            ),
            "core_domain_families": sum(family.core_domain for family in self.families),
            "text_only_families": sum(
                not family.core_domain for family in self.families
            ),
            "balancing_cost": self.cost,
        }


def codex_family_id(record: dict[str, Any]) -> str:
    session_ids = [str(value) for value in record.get("session_ids", [])]
    if session_ids:
        return min(session_ids)
    return Path(str(record["path"])).stem


def claude_family_id(record: dict[str, Any]) -> str:
    path = Path(str(record["path"]))
    parts = path.parts
    try:
        project_index = parts.index("projects")
    except ValueError:
        return path.stem
    if project_index + 1 >= len(parts):
        return path.stem
    project_dir = parts[project_index + 1]
    relative_parts = parts[project_index + 2 :]
    if "subagents" in relative_parts and relative_parts:
        return f"{project_dir}/{relative_parts[0]}"
    return f"{project_dir}/{path.stem}"


def family_id(record: dict[str, Any]) -> str:
    if record.get("harness") == "codex":
        return codex_family_id(record)
    return claude_family_id(record)


def read_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise SystemExit(
                    f"invalid inventory JSON at {path}:{line_number}: {error}"
                ) from error
            if not isinstance(record, dict):
                raise SystemExit(
                    f"inventory row at {path}:{line_number} is not an object"
                )
            harness = record.get("harness")
            if harness not in {"codex", "claude"}:
                raise SystemExit(
                    f"unsupported harness at {path}:{line_number}: {harness!r}"
                )
            if not isinstance(record.get("path"), str):
                raise SystemExit(f"missing path at {path}:{line_number}")
            records.append(record)
    return records


def build_families(records: list[dict[str, Any]]) -> dict[str, list[Family]]:
    grouped: dict[tuple[str, str], Family] = {}
    for record in records:
        key = (str(record["harness"]), family_id(record))
        if key not in grouped:
            grouped[key] = Family(harness=key[0], family_id=key[1])
        grouped[key].records.append(record)
    result: dict[str, list[Family]] = {"codex": [], "claude": []}
    for family in grouped.values():
        result[family.harness].append(family)
    return result


def assign_partitions(families: list[Family], count: int) -> list[Partition]:
    partitions = [Partition(index=index + 1) for index in range(count)]
    ordered = sorted(
        families,
        key=lambda family: (
            -family.cost,
            hashlib.sha256(family.family_id.encode("utf-8")).hexdigest(),
        ),
    )
    for family in ordered:
        target = min(
            partitions, key=lambda partition: (partition.cost, partition.index)
        )
        target.add(family)
    for partition in partitions:
        partition.families.sort(
            key=lambda family: (family.timestamp_min or "", family.family_id)
        )
    return partitions


def write_ndjson(path: Path, documents: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for document in documents:
            json.dump(document, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Group candidate trace rows into balanced family partitions."
    )
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--partitions", type=int, default=6)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace generated partition manifests in the output directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.partitions < 1:
        raise SystemExit("--partitions must be positive")
    inventory = args.inventory.expanduser().resolve()
    if not inventory.is_file():
        raise SystemExit(f"--inventory is not a file: {inventory}")
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_paths = [output_dir / "partition-summary.json"]
    for harness in ("codex", "claude"):
        for index in range(1, args.partitions + 1):
            stem = f"{harness}-{index:02d}"
            generated_paths.extend(
                [output_dir / f"{stem}.ndjson", output_dir / f"{stem}.txt"]
            )
    existing_outputs = [path for path in generated_paths if path.exists()]
    if existing_outputs and not args.replace:
        rendered = ", ".join(str(path) for path in existing_outputs)
        raise SystemExit(
            "generated partition output already exists; choose a new directory or "
            f"pass --replace after authorization: {rendered}"
        )
    families_by_harness = build_families(read_records(inventory))
    summary: dict[str, Any] = {
        "inventory": str(inventory),
        "partition_count_per_harness": args.partitions,
        "harnesses": {},
    }

    for harness in ("codex", "claude"):
        partitions = assign_partitions(families_by_harness[harness], args.partitions)
        harness_summaries = []
        for partition in partitions:
            stem = f"{harness}-{partition.index:02d}"
            documents = [family.as_dict() for family in partition.families]
            write_ndjson(output_dir / f"{stem}.ndjson", documents)
            with (output_dir / f"{stem}.txt").open("w", encoding="utf-8") as handle:
                for document in documents:
                    for file_record in document["files"]:
                        handle.write(str(file_record["path"]) + "\n")
            harness_summaries.append(partition.summary())
        summary["harnesses"][harness] = {
            "families": len(families_by_harness[harness]),
            "partitions": harness_summaries,
        }

    with (output_dir / "partition-summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    print(
        "Wrote "
        f"{len(families_by_harness['codex'])} Codex and "
        f"{len(families_by_harness['claude'])} Claude families across "
        f"{args.partitions} partitions per harness."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
