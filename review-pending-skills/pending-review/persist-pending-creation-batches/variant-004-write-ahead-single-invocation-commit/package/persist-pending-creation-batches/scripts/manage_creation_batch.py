#!/usr/bin/env python3
"""Persist and verify one staged, invocation-wide pending-creation batch."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from typing import Any


MODE = "write-ahead-single-invocation-commit"
SCHEMA_VERSION = 1
RESULT_SCHEMA_VERSION = 1
CANDIDATE_PREFIX = ("review-pending-skills", "pending-review")
NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
DIGEST_RE = re.compile(r"[0-9a-f]{64}\Z")
OID_RE = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
SUPPORTED_MODES = {"100644", "100755", "120000"}


def normalize_home_text(value: str) -> str:
    """Normalize expanded home paths before rendering diagnostics."""

    home = str(Path.home().resolve(strict=False))
    return value.replace(home, "~")


def canonical_json(value: Any) -> str:
    """Serialize deterministic, human-readable JSON."""

    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def sha256_bytes(payload: bytes) -> str:
    """Hash exact bytes."""

    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    """Hash one complete evidence file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def run_git(repo: Path, *arguments: str, check: bool = True) -> bytes:
    """Run one read-only or fixture-owned Git operation with exact output capture."""

    completed = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(
            "git command failed; condition=exit code 0; "
            f"expected=0; received={completed.returncode}; argv={arguments!r}; "
            f"stderr={completed.stderr.decode(errors='replace')!r}"
        )
    return completed.stdout


def current_head(repo: Path) -> str | None:
    """Return `HEAD`, or `None` for an unborn repository."""

    completed = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=repo,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def canonical_candidate_root(value: Any) -> str:
    """Require exactly one canonical pending candidate root."""

    if not isinstance(value, str):
        raise ValueError(f"candidate root must be a string: {value!r}")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or len(path.parts) != 3
        or path.parts[:2] != CANDIDATE_PREFIX
        or NAME_RE.fullmatch(path.parts[2]) is None
    ):
        raise ValueError(
            "candidate root must equal "
            f"review-pending-skills/pending-review/<candidate-name>: {value!r}"
        )
    return value


def canonical_repository_path(value: Any, location: str) -> str:
    """Require a canonical repository-relative pathname."""

    if not isinstance(value, str) or not value:
        raise ValueError(f"{location} must be a nonempty string")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or ".." in path.parts:
        raise ValueError(f"{location} must be repository-relative: {value!r}")
    return value


def repository_relative(repo: Path, path: Path) -> str:
    """Return an existing regular evidence file as a repository-relative path."""

    raw = path.expanduser()
    if raw.is_symlink() or not raw.is_file():
        raise ValueError(f"evidence path is not a regular non-symlink file: {raw}")
    resolved = raw.resolve(strict=True)
    try:
        relative = resolved.relative_to(repo.resolve(strict=True))
    except ValueError as error:
        raise ValueError(f"evidence path is outside the repository: {resolved}") from error
    return canonical_repository_path(relative.as_posix(), "evidence path")


def evidence_path(repo: Path, value: str) -> Path:
    """Resolve one declared evidence path without allowing repository escape."""

    relative = canonical_repository_path(value, "evidence path")
    raw = repo / Path(*PurePosixPath(relative).parts)
    if raw.is_symlink() or not raw.is_file():
        raise ValueError(f"evidence path is not a regular non-symlink file: {relative!r}")
    resolved = raw.resolve(strict=True)
    try:
        resolved.relative_to(repo.resolve(strict=True))
    except ValueError as error:
        raise ValueError(f"evidence path escapes the repository: {relative!r}") from error
    return resolved


def validate_digest(value: Any, location: str) -> str:
    """Require one lowercase SHA-256 digest."""

    if not isinstance(value, str) or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{location} must be a lowercase SHA-256 digest")
    return value


def validate_oid(value: Any, location: str) -> str:
    """Require one Git object identifier."""

    if not isinstance(value, str) or OID_RE.fullmatch(value) is None:
        raise ValueError(f"{location} must be a Git object id")
    return value


def parse_name_status_z(raw: bytes) -> list[dict[str, str | None]]:
    """Parse NUL-delimited name-status records, including rename and copy pairs."""

    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    records: list[dict[str, str | None]] = []
    index = 0
    while index < len(fields):
        status = fields[index].decode("ascii", errors="strict")
        index += 1
        if not status:
            raise ValueError("empty Git name-status value")
        kind = status[0]
        required = 2 if kind in {"R", "C"} else 1
        if index + required > len(fields):
            raise ValueError(f"truncated Git name-status record: {status!r}")
        if required == 2:
            original = fields[index].decode("utf-8", errors="strict")
            path = fields[index + 1].decode("utf-8", errors="strict")
            index += 2
        else:
            original = None
            path = fields[index].decode("utf-8", errors="strict")
            index += 1
        records.append(
            {
                "status": status,
                "kind": kind,
                "path": canonical_repository_path(path, "Git path"),
                "original_path": (
                    canonical_repository_path(original, "Git original path")
                    if original is not None
                    else None
                ),
            }
        )
    return records


def parse_porcelain_v1_z(raw: bytes) -> list[dict[str, str | None]]:
    """Parse NUL-delimited porcelain records and their rename/copy sources."""

    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    records: list[dict[str, str | None]] = []
    index = 0
    while index < len(fields):
        row = fields[index]
        index += 1
        if len(row) < 4 or row[2:3] != b" ":
            raise ValueError("malformed Git porcelain record")
        status = row[:2].decode("ascii", errors="strict")
        path = canonical_repository_path(
            row[3:].decode("utf-8", errors="strict"),
            "Git porcelain path",
        )
        original = None
        if status[0] in {"R", "C"}:
            if index >= len(fields):
                raise ValueError("truncated Git porcelain rename/copy record")
            original = canonical_repository_path(
                fields[index].decode("utf-8", errors="strict"),
                "Git porcelain original path",
            )
            index += 1
        records.append(
            {
                "status": status,
                "kind": status[0],
                "path": path,
                "original_path": original,
            }
        )
    return records


def parse_index_z(raw: bytes) -> list[tuple[str, str, str]]:
    """Parse stage-zero `git ls-files --stage -z` entries."""

    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    entries: list[tuple[str, str, str]] = []
    for field in fields:
        try:
            header, path_bytes = field.split(b"\t", 1)
            mode, oid, stage = header.decode("ascii", errors="strict").split(" ")
        except ValueError as error:
            raise ValueError("malformed staged-index record") from error
        if stage != "0":
            raise ValueError(f"unmerged index stage is not supported: {stage}")
        if mode not in SUPPORTED_MODES:
            raise ValueError(f"unsupported staged object mode: {mode}")
        validate_oid(oid, "staged blob oid")
        path = canonical_repository_path(
            path_bytes.decode("utf-8", errors="strict"),
            "staged path",
        )
        entries.append((mode, oid, path))
    return entries


def parse_tree_z(raw: bytes) -> list[tuple[str, str, str]]:
    """Parse recursive `git ls-tree -z` blob entries."""

    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    entries: list[tuple[str, str, str]] = []
    for field in fields:
        try:
            header, path_bytes = field.split(b"\t", 1)
            mode, object_type, oid = header.decode("ascii", errors="strict").split(" ")
        except ValueError as error:
            raise ValueError("malformed commit-tree record") from error
        if object_type != "blob" or mode not in SUPPORTED_MODES:
            raise ValueError(
                f"unsupported commit-tree object: type={object_type!r}, mode={mode!r}"
            )
        validate_oid(oid, "commit-tree blob oid")
        path = canonical_repository_path(
            path_bytes.decode("utf-8", errors="strict"),
            "commit-tree path",
        )
        entries.append((mode, oid, path))
    return entries


def affected_paths(record: dict[str, str | None]) -> list[str]:
    """Return paths actually changed by one Git record."""

    path = str(record["path"])
    original = record["original_path"]
    if record["kind"] == "R" and isinstance(original, str):
        return [original, path]
    return [path]


def inside(path: str, roots: list[str]) -> bool:
    """Return whether one path belongs to a declared candidate root."""

    return any(path == root or path.startswith(f"{root}/") for root in roots)


def staged_records(repo: Path) -> list[dict[str, str | None]]:
    """Return every staged transition record."""

    return parse_name_status_z(
        run_git(
            repo,
            "diff",
            "--cached",
            "--name-status",
            "-z",
            "--find-renames",
            "--find-copies",
        )
    )


def candidate_status(repo: Path, roots: list[str]) -> list[dict[str, str | None]]:
    """Return exact index/worktree status for declared candidate roots."""

    return parse_porcelain_v1_z(
        run_git(
            repo,
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--",
            *roots,
        )
    )


def candidate_remainder(repo: Path, roots: list[str]) -> list[dict[str, str | None]]:
    """Return untracked or unstaged candidate rows."""

    return [
        record
        for record in candidate_status(repo, roots)
        if record["status"] == "??" or str(record["status"])[1] != " "
    ]


def physical_root_failures(repo: Path, roots: list[str]) -> list[str]:
    """Return missing or symlinked candidate roots."""

    return sorted(
        root for root in roots if (repo / root).is_symlink() or not (repo / root).is_dir()
    )


def staged_scope(
    repo: Path,
    roots: list[str],
) -> tuple[list[dict[str, str | None]], list[str], list[str]]:
    """Return staged records, unrelated paths, and roots without transition coverage."""

    records = staged_records(repo)
    paths = [path for record in records for path in affected_paths(record)]
    outside = sorted(path for path in paths if not inside(path, roots))
    missing_coverage = sorted(
        root for root in roots if not any(inside(path, [root]) for path in paths)
    )
    return records, outside, missing_coverage


def read_blob(repo: Path, oid: str) -> bytes:
    """Read one exact blob by object identifier."""

    return run_git(repo, "cat-file", "blob", oid)


def snapshot_entries(
    repo: Path,
    raw_entries: list[tuple[str, str, str]],
    roots: list[str],
) -> list[dict[str, str | None]]:
    """Describe exact pathname, bytes, mode, and symlink target for Git blobs."""

    snapshot: list[dict[str, str | None]] = []
    for mode, oid, path in raw_entries:
        if not inside(path, roots):
            raise ValueError(f"Git object path is outside declared roots: {path!r}")
        payload = read_blob(repo, oid)
        snapshot.append(
            {
                "blob_oid": oid,
                "blob_sha256": sha256_bytes(payload),
                "mode": mode,
                "path": path,
                "symlink_target": payload.hex() if mode == "120000" else None,
            }
        )
    ordered = sorted(snapshot, key=lambda entry: str(entry["path"]))
    paths = [str(entry["path"]) for entry in ordered]
    if len(set(paths)) != len(paths):
        raise ValueError("Git object snapshot contains duplicate paths")
    return ordered


def index_snapshot(repo: Path, roots: list[str]) -> list[dict[str, str | None]]:
    """Read the complete declared root trees from the Git index."""

    raw = run_git(repo, "ls-files", "--stage", "-z", "--", *roots)
    return snapshot_entries(repo, parse_index_z(raw), roots)


def commit_snapshot(repo: Path, roots: list[str]) -> list[dict[str, str | None]]:
    """Read the complete declared root trees from the current commit."""

    raw = run_git(repo, "ls-tree", "-r", "-z", "HEAD", "--", *roots)
    return snapshot_entries(repo, parse_tree_z(raw), roots)


def evidence_declaration(repo: Path, path: Path) -> dict[str, str]:
    """Build one repository-relative evidence declaration."""

    relative = repository_relative(repo, path)
    return {"path": relative, "sha256": sha256_file(evidence_path(repo, relative))}


def build_manifest(
    *,
    repo: Path,
    inventory: Path,
    roots: list[str],
    validation_reports: list[Path],
) -> dict[str, Any]:
    """Freeze validated evidence and the exact staged-object batch."""

    normalized_roots = sorted(canonical_candidate_root(root) for root in roots)
    if not normalized_roots or len(set(normalized_roots)) != len(normalized_roots):
        raise ValueError("candidate roots must be a nonempty unique set")
    missing_roots = physical_root_failures(repo, normalized_roots)
    if missing_roots:
        raise ValueError(f"candidate roots are missing or malformed: {missing_roots}")
    if not validation_reports:
        raise ValueError("at least one validation report is required")
    reports = [evidence_declaration(repo, report) for report in validation_reports]
    reports.sort(key=lambda item: item["path"])
    if len({item["path"] for item in reports}) != len(reports):
        raise ValueError("validation report paths must be unique")
    records, outside, missing_coverage = staged_scope(repo, normalized_roots)
    remainder = candidate_remainder(repo, normalized_roots)
    snapshot = index_snapshot(repo, normalized_roots)
    snapshot_missing = sorted(
        root
        for root in normalized_roots
        if not any(inside(str(entry["path"]), [root]) for entry in snapshot)
    )
    if not records or outside or missing_coverage or remainder or snapshot_missing:
        raise ValueError(
            "staged batch is incomplete; "
            f"records={len(records)}, outside={outside}, missing_coverage={missing_coverage}, "
            f"remainder={remainder}, snapshot_missing={snapshot_missing}"
        )
    return {
        "candidate_roots": normalized_roots,
        "inventory": evidence_declaration(repo, inventory),
        "precommit_oid": current_head(repo),
        "schema_version": SCHEMA_VERSION,
        "staged_entries": snapshot,
        "validation_reports": reports,
    }


def validate_evidence(value: Any, location: str) -> dict[str, str]:
    """Validate one evidence declaration."""

    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise ValueError(f"{location} must contain exactly path and sha256")
    return {
        "path": canonical_repository_path(value["path"], f"{location}.path"),
        "sha256": validate_digest(value["sha256"], f"{location}.sha256"),
    }


def validate_staged_entry(value: Any, index: int) -> dict[str, str | None]:
    """Validate one staged-object declaration."""

    location = f"staged_entries[{index}]"
    required = {"blob_oid", "blob_sha256", "mode", "path", "symlink_target"}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError(f"{location} keys must equal {sorted(required)}")
    mode = value["mode"]
    if mode not in SUPPORTED_MODES:
        raise ValueError(f"{location}.mode is unsupported: {mode!r}")
    target = value["symlink_target"]
    if mode == "120000":
        if not isinstance(target, str) or re.fullmatch(r"(?:[0-9a-f]{2})*", target) is None:
            raise ValueError(f"{location}.symlink_target must contain lowercase hex bytes")
    elif target is not None:
        raise ValueError(f"{location}.symlink_target must be null for regular files")
    return {
        "blob_oid": validate_oid(value["blob_oid"], f"{location}.blob_oid"),
        "blob_sha256": validate_digest(value["blob_sha256"], f"{location}.blob_sha256"),
        "mode": mode,
        "path": canonical_repository_path(value["path"], f"{location}.path"),
        "symlink_target": target,
    }


def load_manifest(path: Path) -> dict[str, Any]:
    """Load and validate the complete convergence manifest schema."""

    value = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "candidate_roots",
        "inventory",
        "precommit_oid",
        "schema_version",
        "staged_entries",
        "validation_reports",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError(f"manifest keys must equal {sorted(required)}")
    if value["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"schema_version must equal {SCHEMA_VERSION}")
    roots_value = value["candidate_roots"]
    if not isinstance(roots_value, list) or not roots_value:
        raise ValueError("candidate_roots must be a nonempty array")
    roots = [canonical_candidate_root(root) for root in roots_value]
    if roots != sorted(roots) or len(set(roots)) != len(roots):
        raise ValueError("candidate_roots must be sorted and unique")
    entries_value = value["staged_entries"]
    if not isinstance(entries_value, list) or not entries_value:
        raise ValueError("staged_entries must be a nonempty array")
    entries = [validate_staged_entry(entry, index) for index, entry in enumerate(entries_value)]
    paths = [str(entry["path"]) for entry in entries]
    if paths != sorted(paths) or len(set(paths)) != len(paths):
        raise ValueError("staged_entries must be sorted by unique path")
    if any(not inside(path, roots) for path in paths):
        raise ValueError("staged_entries contain paths outside candidate_roots")
    missing_entries = sorted(
        root for root in roots if not any(inside(path, [root]) for path in paths)
    )
    if missing_entries:
        raise ValueError(f"staged_entries omit candidate roots: {missing_entries}")
    reports_value = value["validation_reports"]
    if not isinstance(reports_value, list) or not reports_value:
        raise ValueError("validation_reports must be a nonempty array")
    reports = [
        validate_evidence(report, f"validation_reports[{index}]")
        for index, report in enumerate(reports_value)
    ]
    if reports != sorted(reports, key=lambda item: item["path"]) or len(
        {item["path"] for item in reports}
    ) != len(reports):
        raise ValueError("validation_reports must be sorted by unique path")
    precommit_oid = value["precommit_oid"]
    if precommit_oid is not None:
        precommit_oid = validate_oid(precommit_oid, "precommit_oid")
    return {
        "candidate_roots": roots,
        "inventory": validate_evidence(value["inventory"], "inventory"),
        "precommit_oid": precommit_oid,
        "schema_version": SCHEMA_VERSION,
        "staged_entries": entries,
        "validation_reports": reports,
    }


def create_manifest(path: Path, manifest: dict[str, Any]) -> None:
    """Create an immutable manifest without replacing any existing path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="") as handle:
        handle.write(canonical_json(manifest))
        handle.flush()
        os.fsync(handle.fileno())


def evidence_drift(repo: Path, manifest: dict[str, Any]) -> list[dict[str, str]]:
    """Return evidence declarations whose current bytes differ."""

    drift: list[dict[str, str]] = []
    for declaration in [manifest["inventory"], *manifest["validation_reports"]]:
        try:
            received = sha256_file(evidence_path(repo, declaration["path"]))
        except (OSError, ValueError) as error:
            received = f"unavailable: {error}"
        if received != declaration["sha256"]:
            drift.append(
                {
                    "path": declaration["path"],
                    "expected": declaration["sha256"],
                    "received": received,
                }
            )
    return drift


def verify_precommit(repo: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Require the current index and evidence to equal the immutable manifest."""

    roots = manifest["candidate_roots"]
    records, outside, missing_coverage = staged_scope(repo, roots)
    missing_roots = physical_root_failures(repo, roots)
    remainder = candidate_remainder(repo, roots) if not missing_roots else []
    received_entries = index_snapshot(repo, roots)
    received_precommit = current_head(repo)
    drift = evidence_drift(repo, manifest)
    success = (
        bool(records)
        and not outside
        and not missing_coverage
        and not missing_roots
        and not remainder
        and not drift
        and received_entries == manifest["staged_entries"]
        and received_precommit == manifest["precommit_oid"]
    )
    return {
        "status": "success" if success else "failure",
        "condition": (
            "HEAD, evidence, candidate remainder, and exact staged Git objects equal "
            "the immutable manifest"
        ),
        "expected": {
            "outside": [],
            "missing_coverage": [],
            "missing_roots": [],
            "remainder": [],
            "evidence_drift": [],
            "precommit_oid": manifest["precommit_oid"],
            "staged_entries": manifest["staged_entries"],
        },
        "received": {
            "outside": outside,
            "missing_coverage": missing_coverage,
            "missing_roots": missing_roots,
            "remainder": remainder,
            "evidence_drift": drift,
            "precommit_oid": received_precommit,
            "staged_entries": received_entries,
        },
        "mode": MODE,
    }


def transition_count(repo: Path, precommit_oid: str | None) -> int:
    """Count commits after the manifest's precommit authority."""

    raw = (
        run_git(repo, "rev-list", "--count", "HEAD")
        if precommit_oid is None
        else run_git(repo, "rev-list", "--count", f"{precommit_oid}..HEAD")
    )
    return int(raw.decode().strip())


def transition_records(repo: Path, precommit_oid: str | None) -> list[dict[str, str | None]]:
    """Return every path transition after the manifest's precommit authority."""

    if precommit_oid is None:
        raw = run_git(
            repo,
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-status",
            "-r",
            "-z",
            "--find-renames",
            "--find-copies",
            "HEAD",
        )
    else:
        raw = run_git(
            repo,
            "diff",
            "--name-status",
            "-z",
            "--find-renames",
            "--find-copies",
            f"{precommit_oid}..HEAD",
        )
    return parse_name_status_z(raw)


def verify_postcommit(repo: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Require one transition whose committed root trees equal the staged manifest."""

    roots = manifest["candidate_roots"]
    head = current_head(repo)
    count = 0 if head is None else transition_count(repo, manifest["precommit_oid"])
    records = [] if head is None else transition_records(repo, manifest["precommit_oid"])
    paths = [path for record in records for path in affected_paths(record)]
    outside = sorted(path for path in paths if not inside(path, roots))
    missing_coverage = sorted(
        root for root in roots if not any(inside(path, [root]) for path in paths)
    )
    missing_roots = physical_root_failures(repo, roots)
    remainder = candidate_remainder(repo, roots) if not missing_roots else []
    committed_entries = [] if head is None else commit_snapshot(repo, roots)
    drift = evidence_drift(repo, manifest)
    success = (
        count == 1
        and not outside
        and not missing_coverage
        and not missing_roots
        and not remainder
        and not drift
        and committed_entries == manifest["staged_entries"]
    )
    return {
        "status": "success" if success else "failure",
        "condition": (
            "one commit contains every declared root and the exact staged objects from "
            "the immutable manifest"
        ),
        "expected": {
            "commit_count": 1,
            "outside": [],
            "missing_coverage": [],
            "missing_roots": [],
            "remainder": [],
            "evidence_drift": [],
            "committed_entries": manifest["staged_entries"],
        },
        "received": {
            "commit_count": count,
            "outside": outside,
            "missing_coverage": missing_coverage,
            "missing_roots": missing_roots,
            "remainder": remainder,
            "evidence_drift": drift,
            "committed_entries": committed_entries,
        },
        "commit_oid": head,
        "mode": MODE,
    }


def result_record(
    manifest_path: Path,
    manifest: dict[str, Any],
    postcommit: dict[str, Any],
) -> dict[str, Any]:
    """Build the append-only record for one successful transition."""

    if postcommit["status"] != "success" or postcommit["commit_oid"] is None:
        raise ValueError("cannot record an unsuccessful postcommit transition")
    return {
        "candidate_roots": manifest["candidate_roots"],
        "commit_oid": postcommit["commit_oid"],
        "manifest_sha256": sha256_file(manifest_path),
        "precommit_oid": manifest["precommit_oid"],
        "schema_version": RESULT_SCHEMA_VERSION,
    }


def append_result(path: Path, record: dict[str, Any]) -> None:
    """Append one result without rewriting existing records."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not line.strip():
                continue
            try:
                existing = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"result JSONL is malformed at line {line_number}: {error}"
                ) from error
            if not isinstance(existing, dict):
                raise ValueError(f"result JSONL line {line_number} is not an object")
            if existing.get("manifest_sha256") == record["manifest_sha256"]:
                raise ValueError("result already exists for this immutable manifest")
    serialized = json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n"
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, "a", encoding="utf-8", newline="") as handle:
        handle.write(serialized)
        handle.flush()
        os.fsync(handle.fileno())


def write_candidate(repo: Path, root: str) -> tuple[Path, Path, Path]:
    """Create regular, executable, and symlink fixture entries."""

    package = repo / root / "variant-001" / "package"
    package.mkdir(parents=True, exist_ok=True)
    intent = package / "intent.md"
    executable = package / "check.sh"
    link = package / "current"
    intent.write_text("intent\n", encoding="utf-8")
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    link.symlink_to("intent.md")
    return intent, executable, link


def fixture_commit(repo: Path, message: str) -> None:
    """Commit disposable fixture state without invoking external hooks."""

    run_git(
        repo,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "-c",
        "core.hooksPath=/dev/null",
        "commit",
        "--quiet",
        "-m",
        message,
    )


def expect_value_error(operation: Any, message: str) -> None:
    """Require one callable to reject its input."""

    try:
        operation()
    except (FileExistsError, ValueError):
        return
    raise AssertionError(message)


def self_test() -> dict[str, Any]:
    """Exercise staged-object evidence and every load-bearing failure path."""

    assertions = 0
    with tempfile.TemporaryDirectory() as temporary:
        repo = Path(temporary)
        run_git(repo, "init", "--quiet", "--initial-branch=main")
        (repo / "baseline.txt").write_text("baseline\n", encoding="utf-8")
        run_git(repo, "add", "baseline.txt")
        fixture_commit(repo, "baseline")

        scratch = repo / ".scratchpad" / "batch"
        scratch.mkdir(parents=True)
        inventory = scratch / "inventory.json"
        validation = scratch / "validation.json"
        inventory.write_text('{"candidate_count": 2}\n', encoding="utf-8")
        validation.write_text('{"status": "passed"}\n', encoding="utf-8")
        roots = [
            "review-pending-skills/pending-review/a",
            "review-pending-skills/pending-review/b",
        ]
        first_files = write_candidate(repo, roots[0])
        second_files = write_candidate(repo, roots[1])

        missing_root = "review-pending-skills/pending-review/c"
        write_candidate(repo, missing_root)
        expect_value_error(
            lambda: build_manifest(
                repo=repo,
                inventory=inventory,
                roots=[*roots, missing_root],
                validation_reports=[validation],
            ),
            "an unstaged root was accepted",
        )
        shutil.rmtree(repo / missing_root)
        assertions += 1

        run_git(repo, "add", "--", *roots)
        first = build_manifest(
            repo=repo,
            inventory=inventory,
            roots=roots,
            validation_reports=[validation],
        )
        second = build_manifest(
            repo=repo,
            inventory=inventory,
            roots=list(reversed(roots)),
            validation_reports=[validation],
        )
        assert first == second
        assertions += 1
        modes = {entry["mode"] for entry in first["staged_entries"]}
        targets = [
            entry["symlink_target"]
            for entry in first["staged_entries"]
            if entry["mode"] == "120000"
        ]
        assert modes == SUPPORTED_MODES and targets == ["696e74656e742e6d64"] * 2
        assertions += 1

        manifest_path = scratch / "manifest.json"
        create_manifest(manifest_path, first)
        loaded = load_manifest(manifest_path)
        assert loaded == first
        assertions += 1
        expect_value_error(
            lambda: create_manifest(manifest_path, first),
            "an immutable manifest was overwritten",
        )
        assertions += 1
        assert verify_precommit(repo, loaded)["status"] == "success"
        assertions += 1

        first_files[0].write_text("worktree drift\n", encoding="utf-8")
        drift = verify_precommit(repo, loaded)
        assert drift["status"] == "failure" and drift["received"]["remainder"]
        first_files[0].write_text("intent\n", encoding="utf-8")
        assert verify_precommit(repo, loaded)["status"] == "success"
        assertions += 1

        unrelated = repo / "unrelated.txt"
        unrelated.write_text("unrelated\n", encoding="utf-8")
        run_git(repo, "add", "unrelated.txt")
        outside = verify_precommit(repo, loaded)
        assert outside["status"] == "failure" and outside["received"]["outside"]
        run_git(repo, "reset", "--", "unrelated.txt")
        unrelated.unlink()
        assertions += 1

        first_files[0].write_text("staged drift\n", encoding="utf-8")
        run_git(repo, "add", "--", str(first_files[0].relative_to(repo)))
        staged_drift = verify_precommit(repo, loaded)
        assert staged_drift["status"] == "failure"
        assert staged_drift["received"]["staged_entries"] != loaded["staged_entries"]
        first_files[0].write_text("intent\n", encoding="utf-8")
        run_git(repo, "add", "--", str(first_files[0].relative_to(repo)))
        assert verify_precommit(repo, loaded)["status"] == "success"
        assertions += 1

        first_files[1].chmod(0o644)
        run_git(repo, "add", "--", str(first_files[1].relative_to(repo)))
        assert verify_precommit(repo, loaded)["status"] == "failure"
        first_files[1].chmod(0o755)
        run_git(repo, "add", "--", str(first_files[1].relative_to(repo)))
        assert verify_precommit(repo, loaded)["status"] == "success"
        assertions += 1

        first_files[2].unlink()
        first_files[2].symlink_to("check.sh")
        run_git(repo, "add", "--", str(first_files[2].relative_to(repo)))
        symlink_drift = verify_precommit(repo, loaded)
        assert symlink_drift["status"] == "failure"
        first_files[2].unlink()
        first_files[2].symlink_to("intent.md")
        run_git(repo, "add", "--", str(first_files[2].relative_to(repo)))
        assert verify_precommit(repo, loaded)["status"] == "success"
        assertions += 1

        validation.write_text('{"status": "changed"}\n', encoding="utf-8")
        evidence_failure = verify_precommit(repo, loaded)
        assert evidence_failure["status"] == "failure"
        assert evidence_failure["received"]["evidence_drift"]
        validation.write_text('{"status": "passed"}\n', encoding="utf-8")
        assert verify_precommit(repo, loaded)["status"] == "success"
        assertions += 1

        hidden = repo / f"{roots[1]}-hidden"
        (repo / roots[1]).rename(hidden)
        missing = verify_precommit(repo, loaded)
        assert missing["status"] == "failure" and missing["received"]["missing_roots"]
        hidden.rename(repo / roots[1])
        assert verify_precommit(repo, loaded)["status"] == "success"
        assertions += 1

        expect_value_error(
            lambda: canonical_candidate_root(
                "review-pending-skills/pending-review/a/variant-001"
            ),
            "a descendant candidate path was accepted",
        )
        assertions += 1
        parsed = parse_name_status_z(b"R100\0old\0new\0C100\0source\0copy\0")
        assert [record["path"] for record in parsed] == ["new", "copy"]
        assert affected_paths(parsed[0]) == ["old", "new"]
        assert affected_paths(parsed[1]) == ["copy"]
        assertions += 1

        invalid = dict(first)
        invalid["schema_version"] = 2
        invalid_path = scratch / "invalid.json"
        invalid_path.write_text(canonical_json(invalid), encoding="utf-8")
        expect_value_error(
            lambda: load_manifest(invalid_path),
            "an invalid manifest schema was accepted",
        )
        assertions += 1

        fixture_commit(repo, "one creation batch")
        postcommit = verify_postcommit(repo, loaded)
        assert postcommit["status"] == "success"
        assert postcommit["received"]["committed_entries"] == loaded["staged_entries"]
        assertions += 1
        record = result_record(manifest_path, loaded, postcommit)
        result_path = scratch / "result.jsonl"
        append_result(result_path, record)
        lines = result_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1 and json.loads(lines[0]) == record
        assertions += 1
        expect_value_error(
            lambda: append_result(result_path, record),
            "a duplicate result record was appended",
        )
        assertions += 1

        split_inventory = scratch / "split-inventory.json"
        split_validation = scratch / "split-validation.json"
        split_inventory.write_text('{"candidate_count": 2}\n', encoding="utf-8")
        split_validation.write_text('{"status": "passed"}\n', encoding="utf-8")
        first_files[0].write_text("split a\n", encoding="utf-8")
        second_files[0].write_text("split b\n", encoding="utf-8")
        run_git(repo, "add", "--", *roots)
        split_manifest = build_manifest(
            repo=repo,
            inventory=split_inventory,
            roots=roots,
            validation_reports=[split_validation],
        )
        split_path = scratch / "split-manifest.json"
        create_manifest(split_path, split_manifest)
        run_git(repo, "reset", "--", roots[1])
        fixture_commit(repo, "split first root")
        run_git(repo, "add", "--", roots[1])
        fixture_commit(repo, "split second root")
        split_postcommit = verify_postcommit(repo, split_manifest)
        assert split_postcommit["status"] == "failure"
        assert split_postcommit["received"]["commit_count"] == 2
        assertions += 1

    return {"status": "passed", "assertions": assertions, "mode": MODE}


def parse_args() -> argparse.Namespace:
    """Parse one lifecycle action or the packaged self-test."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    subparsers = parser.add_subparsers(dest="action")

    create = subparsers.add_parser("create")
    create.add_argument("--repo", type=Path, required=True)
    create.add_argument("--inventory", type=Path, required=True)
    create.add_argument("--candidate-root", action="append", required=True)
    create.add_argument("--validation-report", type=Path, action="append", required=True)
    create.add_argument("--output", type=Path, required=True)

    verify = subparsers.add_parser("verify-precommit")
    verify.add_argument("--repo", type=Path, required=True)
    verify.add_argument("--manifest", type=Path, required=True)

    record = subparsers.add_parser("record-postcommit")
    record.add_argument("--repo", type=Path, required=True)
    record.add_argument("--manifest", type=Path, required=True)
    record.add_argument("--result", type=Path, required=True)

    arguments = parser.parse_args()
    if not arguments.self_test and arguments.action is None:
        parser.error(
            "choose create, verify-precommit, or record-postcommit unless --self-test is used"
        )
    return arguments


def main() -> int:
    """Execute one lifecycle action with machine-readable output."""

    arguments = parse_args()
    try:
        if arguments.self_test:
            output = self_test()
        elif arguments.action == "create":
            repo = arguments.repo.expanduser().resolve(strict=True)
            output = build_manifest(
                repo=repo,
                inventory=arguments.inventory,
                roots=arguments.candidate_root,
                validation_reports=arguments.validation_report,
            )
            create_manifest(arguments.output.expanduser(), output)
        elif arguments.action == "verify-precommit":
            repo = arguments.repo.expanduser().resolve(strict=True)
            output = verify_precommit(
                repo,
                load_manifest(arguments.manifest.expanduser()),
            )
        else:
            repo = arguments.repo.expanduser().resolve(strict=True)
            manifest_path = arguments.manifest.expanduser().resolve(strict=True)
            manifest = load_manifest(manifest_path)
            postcommit = verify_postcommit(repo, manifest)
            if postcommit["status"] == "failure":
                output = postcommit
            else:
                output = result_record(manifest_path, manifest, postcommit)
                append_result(arguments.result.expanduser(), output)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        output = {
            "status": "failure",
            "condition": (
                "the staged-object creation-batch lifecycle completes with exact immutable evidence"
            ),
            "expected": "a valid staged batch, one commit, and an append-only result",
            "received": normalize_home_text(str(error)),
            "mode": MODE,
        }
        print(canonical_json(output), end="")
        return 2
    print(canonical_json(output), end="")
    return 0 if output.get("status", "success") != "failure" else 1


if __name__ == "__main__":
    raise SystemExit(main())
