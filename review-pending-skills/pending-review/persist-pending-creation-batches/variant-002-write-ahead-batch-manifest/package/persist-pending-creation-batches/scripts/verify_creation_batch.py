#!/usr/bin/env python3
"""Create, verify, and complete a write-ahead candidate-root manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import tempfile
from typing import Any


MODE = "write-ahead-batch-manifest"
SCHEMA_VERSION = 2
RESULT_SCHEMA_VERSION = 1
CANDIDATE_PREFIX = ("review-pending-skills", "pending-review")
NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
DIGEST_RE = re.compile(r"[0-9a-f]{64}\Z")
OID_RE = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")


def normalize_home_text(value: str) -> str:
    """Normalize expanded home paths in serialized diagnostics."""

    home = str(Path.home().resolve(strict=False))
    return value.replace(home, "~")


def canonical_json(value: Any) -> str:
    """Serialize deterministic human-readable JSON."""

    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def sha256_file(path: Path) -> str:
    """Hash one complete evidence file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def run_git(repo: Path, *arguments: str, check: bool = True) -> bytes:
    """Run one Git query with exact output capture."""

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
            f"git command failed; condition=exit code 0; expected=0; received={completed.returncode}; "
            f"argv={arguments!r}; stderr={completed.stderr.decode(errors='replace')!r}"
        )
    return completed.stdout


def current_head(repo: Path) -> str | None:
    """Return `HEAD` or `None` for an unborn repository."""

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
    """Require exactly one pending candidate root."""

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


def repository_relative(repo: Path, path: Path) -> str:
    """Return one existing regular evidence file as a repository-relative path."""

    raw = path.expanduser()
    if raw.is_symlink() or not raw.is_file():
        raise ValueError(f"evidence path is not a regular non-symlink file: {raw}")
    resolved = raw.resolve(strict=True)
    try:
        relative = resolved.relative_to(repo.resolve())
    except ValueError as error:
        raise ValueError(f"evidence path is outside the repository: {resolved}") from error
    return relative.as_posix()


def evidence_path(repo: Path, value: str) -> Path:
    """Resolve a canonical repository-relative evidence path."""

    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or ".." in path.parts:
        raise ValueError(f"evidence path must be repository-relative: {value!r}")
    raw = repo / Path(*path.parts)
    if raw.is_symlink() or not raw.is_file():
        raise ValueError(f"evidence path is not a regular non-symlink file: {value!r}")
    resolved = raw.resolve(strict=True)
    try:
        resolved.relative_to(repo.resolve())
    except ValueError as error:
        raise ValueError(f"evidence path escapes the repository: {value!r}") from error
    return resolved


def tree_hash(root: Path) -> str:
    """Hash paths, file bytes, executable modes, and symlink targets."""

    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"candidate root is missing or not a real directory: {root}")
    entries: list[tuple[str, str, bytes]] = []
    for directory, names, filenames in os.walk(root, followlinks=False):
        parent = Path(directory)
        for name in [*names, *filenames]:
            path = parent / name
            relative = path.relative_to(root).as_posix()
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                entries.append((relative, "120000", os.readlink(path).encode()))
            elif stat.S_ISREG(metadata.st_mode):
                mode = "100755" if metadata.st_mode & stat.S_IXUSR else "100644"
                entries.append((relative, mode, path.read_bytes()))
            elif stat.S_ISDIR(metadata.st_mode):
                continue
            else:
                raise ValueError(f"unsupported candidate entry type: {relative}")
    digest = hashlib.sha256()
    for relative, mode, payload in sorted(entries):
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(mode.encode())
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return digest.hexdigest()


def build_manifest(
    *,
    repo: Path,
    inventory: Path,
    roots: list[str],
    validation_reports: list[Path],
) -> dict[str, Any]:
    """Freeze one deterministic precommit evidence document."""

    normalized_roots = sorted(canonical_candidate_root(root) for root in roots)
    if not normalized_roots or len(set(normalized_roots)) != len(normalized_roots):
        raise ValueError("candidate roots must be a nonempty unique set")
    missing = [
        root
        for root in normalized_roots
        if (repo / root).is_symlink() or not (repo / root).is_dir()
    ]
    if missing:
        raise ValueError(f"candidate roots are missing or malformed: {missing}")
    if not validation_reports:
        raise ValueError("at least one validation report is required")
    inventory_relative = repository_relative(repo, inventory)
    reports = [
        {
            "path": repository_relative(repo, report),
            "sha256": sha256_file(report.expanduser().resolve(strict=True)),
        }
        for report in validation_reports
    ]
    reports.sort(key=lambda item: item["path"])
    if len({item["path"] for item in reports}) != len(reports):
        raise ValueError("validation report paths must be unique")
    return {
        "candidate_roots": normalized_roots,
        "inventory": {
            "path": inventory_relative,
            "sha256": sha256_file(inventory.expanduser().resolve(strict=True)),
        },
        "precommit_oid": current_head(repo),
        "schema_version": SCHEMA_VERSION,
        "tree_hashes": {root: tree_hash(repo / root) for root in normalized_roots},
        "validation_reports": reports,
    }


def validate_digest(value: Any, location: str) -> str:
    """Require one lowercase SHA-256 digest."""

    if not isinstance(value, str) or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{location} must be a lowercase SHA-256 digest")
    return value


def load_manifest(path: Path) -> dict[str, Any]:
    """Validate the complete version-two manifest schema."""

    value = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "candidate_roots",
        "inventory",
        "precommit_oid",
        "schema_version",
        "tree_hashes",
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
    tree_hashes = value["tree_hashes"]
    if not isinstance(tree_hashes, dict) or set(tree_hashes) != set(roots):
        raise ValueError("tree_hashes keys must equal candidate_roots")
    normalized_hashes = {
        root: validate_digest(tree_hashes[root], f"tree_hashes[{root!r}]") for root in roots
    }
    inventory = value["inventory"]
    if not isinstance(inventory, dict) or set(inventory) != {"path", "sha256"}:
        raise ValueError("inventory must contain exactly path and sha256")
    if not isinstance(inventory["path"], str):
        raise ValueError("inventory.path must be a string")
    normalized_inventory = {
        "path": inventory["path"],
        "sha256": validate_digest(inventory["sha256"], "inventory.sha256"),
    }
    reports_value = value["validation_reports"]
    if not isinstance(reports_value, list) or not reports_value:
        raise ValueError("validation_reports must be a nonempty array")
    reports: list[dict[str, str]] = []
    for index, report in enumerate(reports_value):
        if not isinstance(report, dict) or set(report) != {"path", "sha256"}:
            raise ValueError(f"validation_reports[{index}] must contain path and sha256")
        if not isinstance(report["path"], str):
            raise ValueError(f"validation_reports[{index}].path must be a string")
        reports.append(
            {
                "path": report["path"],
                "sha256": validate_digest(report["sha256"], f"validation_reports[{index}].sha256"),
            }
        )
    if reports != sorted(reports, key=lambda item: item["path"]) or len(
        {item["path"] for item in reports}
    ) != len(reports):
        raise ValueError("validation_reports must be sorted by unique path")
    precommit_oid = value["precommit_oid"]
    if precommit_oid is not None and (
        not isinstance(precommit_oid, str) or OID_RE.fullmatch(precommit_oid) is None
    ):
        raise ValueError("precommit_oid must be null or a Git object id")
    return {
        "candidate_roots": roots,
        "inventory": normalized_inventory,
        "precommit_oid": precommit_oid,
        "schema_version": SCHEMA_VERSION,
        "tree_hashes": normalized_hashes,
        "validation_reports": reports,
    }


def create_manifest(path: Path, manifest: dict[str, Any]) -> None:
    """Create an immutable manifest without replacing an existing path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="") as handle:
        handle.write(canonical_json(manifest))
        handle.flush()
        os.fsync(handle.fileno())


def parse_name_status_z(raw: bytes) -> list[dict[str, str | None]]:
    """Parse Git name-status records, consuming rename and copy path pairs."""

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
            original = fields[index].decode(errors="surrogateescape")
            path = fields[index + 1].decode(errors="surrogateescape")
            index += 2
        else:
            original = None
            path = fields[index].decode(errors="surrogateescape")
            index += 1
        records.append({"status": status, "kind": kind, "path": path, "original_path": original})
    return records


def parse_porcelain_v1_z(raw: bytes) -> list[dict[str, str | None]]:
    """Parse candidate status and consume rename/copy source fields."""

    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    records: list[dict[str, str | None]] = []
    index = 0
    while index < len(fields):
        row = fields[index]
        index += 1
        if len(row) < 3 or row[2:3] != b" ":
            raise ValueError("malformed Git porcelain record")
        status = row[:2].decode("ascii", errors="strict")
        path = row[3:].decode(errors="surrogateescape")
        original = None
        if status[0] in {"R", "C"}:
            if index >= len(fields):
                raise ValueError("truncated Git porcelain rename/copy record")
            original = fields[index].decode(errors="surrogateescape")
            index += 1
        records.append({"status": status, "kind": status[0], "path": path, "original_path": original})
    return records


def affected_paths(record: dict[str, str | None]) -> list[str]:
    """Return paths actually changed by one Git record."""

    path = str(record["path"])
    original = record["original_path"]
    return [str(original), path] if record["kind"] == "R" and isinstance(original, str) else [path]


def inside(path: str, roots: list[str]) -> bool:
    """Return whether one path belongs to a declared root."""

    return any(path == root or path.startswith(f"{root}/") for root in roots)


def staged_records(repo: Path) -> list[dict[str, str | None]]:
    """Return complete staged name-status records."""

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
    """Return exact index/worktree status for candidate roots."""

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


def evidence_drift(repo: Path, manifest: dict[str, Any]) -> list[dict[str, str]]:
    """Return evidence files whose current hash differs from the manifest."""

    declarations = [manifest["inventory"], *manifest["validation_reports"]]
    drift: list[dict[str, str]] = []
    for declaration in declarations:
        try:
            path = evidence_path(repo, declaration["path"])
            received = sha256_file(path)
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


def remainder(repo: Path, roots: list[str]) -> list[dict[str, str | None]]:
    """Return untracked or unstaged candidate rows."""

    return [
        record
        for record in candidate_status(repo, roots)
        if record["status"] == "??" or str(record["status"])[1] != " "
    ]


def verify(repo: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Compare staged names and current evidence to the write-ahead manifest."""

    roots = manifest["candidate_roots"]
    records = staged_records(repo)
    paths = [path for record in records for path in affected_paths(record)]
    outside = sorted(path for path in paths if not inside(path, roots))
    missing_roots = sorted(
        root for root in roots if (repo / root).is_symlink() or not (repo / root).is_dir()
    )
    missing_coverage = sorted(root for root in roots if not any(inside(path, [root]) for path in paths))
    received_hashes = {
        root: tree_hash(repo / root) for root in roots if root not in missing_roots
    }
    candidate_remainder = remainder(repo, roots) if not missing_roots else []
    drift = evidence_drift(repo, manifest)
    received_precommit = current_head(repo)
    success = (
        bool(records)
        and not outside
        and not missing_roots
        and not missing_coverage
        and not candidate_remainder
        and not drift
        and received_hashes == manifest["tree_hashes"]
        and received_precommit == manifest["precommit_oid"]
    )
    return {
        "status": "success" if success else "failure",
        "condition": "staged roots, current bytes, evidence hashes, and HEAD equal the immutable manifest",
        "expected": {
            "outside": [],
            "missing_roots": [],
            "missing_coverage": [],
            "remainder": [],
            "evidence_drift": [],
            "tree_hashes": manifest["tree_hashes"],
            "precommit_oid": manifest["precommit_oid"],
        },
        "received": {
            "outside": outside,
            "missing_roots": missing_roots,
            "missing_coverage": missing_coverage,
            "remainder": candidate_remainder,
            "evidence_drift": drift,
            "tree_hashes": received_hashes,
            "precommit_oid": received_precommit,
        },
        "mode": MODE,
    }


def transition_count(repo: Path, precommit_oid: str | None) -> int:
    """Count commits since the manifest's precommit authority."""

    raw = (
        run_git(repo, "rev-list", "--count", "HEAD")
        if precommit_oid is None
        else run_git(repo, "rev-list", "--count", f"{precommit_oid}..HEAD")
    )
    return int(raw.decode().strip())


def transition_records(repo: Path, precommit_oid: str | None) -> list[dict[str, str | None]]:
    """Return the complete path transition after the write-ahead manifest."""

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


def postcommit_record(repo: Path, manifest_path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Require one complete commit and build its append-only result record."""

    head = current_head(repo)
    count = 0 if head is None else transition_count(repo, manifest["precommit_oid"])
    records = [] if head is None else transition_records(repo, manifest["precommit_oid"])
    paths = [path for record in records for path in affected_paths(record)]
    outside = sorted(path for path in paths if not inside(path, manifest["candidate_roots"]))
    missing = sorted(
        root
        for root in manifest["candidate_roots"]
        if not any(inside(path, [root]) for path in paths)
    )
    missing_roots = sorted(
        root
        for root in manifest["candidate_roots"]
        if (repo / root).is_symlink() or not (repo / root).is_dir()
    )
    received_hashes = {
        root: tree_hash(repo / root)
        for root in manifest["candidate_roots"]
        if root not in missing_roots
    }
    drift = evidence_drift(repo, manifest)
    if (
        count != 1
        or outside
        or missing
        or missing_roots
        or received_hashes != manifest["tree_hashes"]
        or drift
    ):
        raise ValueError(
            "postcommit transition failed; "
            "expected one commit with all roots, unchanged evidence, and matching trees; received="
            f"commit_count={count}, outside={outside}, missing={missing}, "
            f"missing_roots={missing_roots}, tree_hashes={received_hashes}, evidence_drift={drift}"
        )
    if remainder(repo, manifest["candidate_roots"]):
        raise ValueError("postcommit candidate remainder is not empty")
    return {
        "candidate_roots": manifest["candidate_roots"],
        "commit_oid": head,
        "manifest_sha256": sha256_file(manifest_path),
        "precommit_oid": manifest["precommit_oid"],
        "schema_version": RESULT_SCHEMA_VERSION,
    }


def append_result(path: Path, record: dict[str, Any]) -> None:
    """Append one result without rewriting existing records."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
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


def write_candidate(repo: Path, root: str, text: str = "intent\n") -> Path:
    """Create one candidate fixture file."""

    path = repo / root / "variant-001" / "intent.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def fixture_commit(repo: Path, message: str) -> None:
    """Commit fixture state without external hooks."""

    run_git(
        repo,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "--quiet",
        "-m",
        message,
    )


def self_test() -> dict[str, Any]:
    """Exercise the full immutable-manifest lifecycle and its negative paths."""

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
        paths = [write_candidate(repo, root) for root in roots]
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
        manifest_path = scratch / "manifest.json"
        create_manifest(manifest_path, first)
        loaded = load_manifest(manifest_path)
        assert loaded == first
        assertions += 1
        try:
            create_manifest(manifest_path, first)
        except FileExistsError:
            assertions += 1
        else:
            raise AssertionError("immutable manifest was overwritten")

        run_git(repo, "add", "--", roots[0])
        assert verify(repo, loaded)["status"] == "failure"
        assertions += 1
        run_git(repo, "add", "--", roots[1])
        assert verify(repo, loaded)["status"] == "success"
        assertions += 1

        paths[0].write_text("drift\n", encoding="utf-8")
        drift = verify(repo, loaded)
        assert drift["status"] == "failure" and drift["received"]["remainder"]
        assertions += 1
        paths[0].write_text("intent\n", encoding="utf-8")
        assert verify(repo, loaded)["status"] == "success"
        assertions += 1

        unrelated = repo / "unrelated.txt"
        unrelated.write_text("unrelated\n", encoding="utf-8")
        run_git(repo, "add", "unrelated.txt")
        assert verify(repo, loaded)["status"] == "failure"
        assertions += 1
        run_git(repo, "reset", "--", "unrelated.txt")
        unrelated.unlink()

        validation.write_text('{"status": "changed"}\n', encoding="utf-8")
        assert verify(repo, loaded)["received"]["evidence_drift"]
        assertions += 1
        validation.write_text('{"status": "passed"}\n', encoding="utf-8")
        assert verify(repo, loaded)["status"] == "success"
        assertions += 1

        fixture_commit(repo, "one batch")
        record = postcommit_record(repo, manifest_path, loaded)
        result_path = scratch / "result.jsonl"
        append_result(result_path, record)
        result_lines = result_path.read_text(encoding="utf-8").splitlines()
        assert len(result_lines) == 1 and json.loads(result_lines[0]) == record
        assertions += 1
        try:
            append_result(result_path, record)
        except ValueError:
            assertions += 1
        else:
            raise AssertionError("duplicate result was appended for one manifest")

        split_inventory = scratch / "split-inventory.json"
        split_validation = scratch / "split-validation.json"
        split_inventory.write_text('{"candidate_count": 2}\n', encoding="utf-8")
        split_validation.write_text('{"status": "passed"}\n', encoding="utf-8")
        split_manifest = build_manifest(
            repo=repo,
            inventory=split_inventory,
            roots=roots,
            validation_reports=[split_validation],
        )
        split_path = scratch / "split-manifest.json"
        create_manifest(split_path, split_manifest)
        paths[0].write_text("split-a\n", encoding="utf-8")
        run_git(repo, "add", "--", roots[0])
        fixture_commit(repo, "split a")
        paths[1].write_text("split-b\n", encoding="utf-8")
        run_git(repo, "add", "--", roots[1])
        fixture_commit(repo, "split b")
        try:
            postcommit_record(repo, split_path, split_manifest)
        except ValueError:
            assertions += 1
        else:
            raise AssertionError("multi-commit transition was accepted")

        invalid = dict(first)
        invalid["schema_version"] = 1
        invalid_path = scratch / "invalid.json"
        invalid_path.write_text(canonical_json(invalid), encoding="utf-8")
        try:
            load_manifest(invalid_path)
        except ValueError:
            assertions += 1
        else:
            raise AssertionError("invalid manifest schema was accepted")

        parsed = parse_name_status_z(b"R100\0old\0new\0C100\0source\0copy\0")
        assert [item["path"] for item in parsed] == ["new", "copy"]
        assertions += 1
    return {"status": "passed", "assertions": assertions, "mode": MODE}


def parse_args() -> argparse.Namespace:
    """Parse one manifest-lifecycle action or the compatibility self-test flag."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    subparsers = parser.add_subparsers(dest="action")

    create = subparsers.add_parser("create")
    create.add_argument("--repo", type=Path, required=True)
    create.add_argument("--inventory", type=Path, required=True)
    create.add_argument("--candidate-root", action="append", required=True)
    create.add_argument("--validation-report", type=Path, action="append", required=True)
    create.add_argument("--output", type=Path, required=True)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--repo", type=Path, required=True)
    verify_parser.add_argument("--manifest", type=Path, required=True)

    record = subparsers.add_parser("record-commit")
    record.add_argument("--repo", type=Path, required=True)
    record.add_argument("--manifest", type=Path, required=True)
    record.add_argument("--result", type=Path, required=True)

    arguments = parser.parse_args()
    if not arguments.self_test and arguments.action is None:
        parser.error("choose create, verify, or record-commit unless --self-test is used")
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
        elif arguments.action == "verify":
            repo = arguments.repo.expanduser().resolve(strict=True)
            output = verify(repo, load_manifest(arguments.manifest.expanduser()))
        else:
            repo = arguments.repo.expanduser().resolve(strict=True)
            manifest_path = arguments.manifest.expanduser().resolve(strict=True)
            manifest = load_manifest(manifest_path)
            output = postcommit_record(repo, manifest_path, manifest)
            append_result(arguments.result.expanduser(), output)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(
            canonical_json(
                {
                    "status": "failure",
                    "condition": "write-ahead manifest lifecycle completes without invalid or stale evidence",
                    "expected": "valid immutable manifest and one commit",
                    "received": normalize_home_text(str(error)),
                    "mode": MODE,
                }
            ),
            end="",
        )
        return 2
    print(canonical_json(output), end="")
    return 0 if output.get("status", "success") != "failure" else 1


if __name__ == "__main__":
    raise SystemExit(main())
