#!/usr/bin/env python3
"""Verify a complete pending-candidate Git batch across one commit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from typing import Any


MODE = "single-invocation-commit"
CANDIDATE_PREFIX = ("review-pending-skills", "pending-review")
NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
OID_RE = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")


def normalize_home_text(value: str) -> str:
    """Normalize expanded home paths in diagnostics."""

    home = str(Path.home().resolve(strict=False))
    return value.replace(home, "~")


def run_git(repo: Path, *arguments: str, check: bool = True) -> bytes:
    """Run one Git query and retain exact NUL-delimited output."""

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


def decode_path(value: bytes) -> str:
    """Decode a Git pathname without losing undecodable bytes."""

    return value.decode(errors="surrogateescape")


def canonical_candidate_root(value: Any) -> str:
    """Require exactly `review-pending-skills/pending-review/<candidate>`."""

    if not isinstance(value, str):
        raise ValueError(f"candidate root check failed; expected=string; received={value!r}")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or len(path.parts) != 3
        or path.parts[:2] != CANDIDATE_PREFIX
        or NAME_RE.fullmatch(path.parts[2]) is None
    ):
        raise ValueError(
            "candidate root check failed; "
            "expected=review-pending-skills/pending-review/<candidate-name>; "
            f"received={value!r}"
        )
    return value


def load_manifest(path: Path) -> dict[str, Any]:
    """Load exact candidate roots and their precommit authority."""

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != {"candidate_roots", "precommit_oid"}:
        raise ValueError(
            "creation manifest shape failed; expected=candidate_roots and precommit_oid"
        )
    roots_value = value["candidate_roots"]
    if not isinstance(roots_value, list) or not roots_value:
        raise ValueError(
            "candidate root check failed; expected=nonempty string list; received=invalid"
        )
    roots = [canonical_candidate_root(root) for root in roots_value]
    if len(set(roots)) != len(roots):
        raise ValueError("candidate root uniqueness check failed; expected=unique; received=duplicates")
    precommit_oid = value["precommit_oid"]
    if precommit_oid is not None and (
        not isinstance(precommit_oid, str) or OID_RE.fullmatch(precommit_oid) is None
    ):
        raise ValueError(
            f"precommit oid check failed; expected=null or Git object id; received={precommit_oid!r}"
        )
    return {"candidate_roots": sorted(roots), "precommit_oid": precommit_oid}


def inside(path: str, roots: list[str]) -> bool:
    """Return whether one repository-relative path belongs to a declared root."""

    return any(path == root or path.startswith(f"{root}/") for root in roots)


def parse_name_status_z(raw: bytes) -> list[dict[str, str | None]]:
    """Parse NUL-delimited Git name-status, including rename and copy pairs."""

    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    records: list[dict[str, str | None]] = []
    index = 0
    while index < len(fields):
        status = fields[index].decode("ascii", errors="strict")
        index += 1
        if not status:
            raise ValueError("Git name-status record has an empty status")
        kind = status[0]
        required = 2 if kind in {"R", "C"} else 1
        if index + required > len(fields):
            raise ValueError(f"Git name-status record is truncated: {status!r}")
        if required == 2:
            original_path = decode_path(fields[index])
            path = decode_path(fields[index + 1])
            index += 2
        else:
            original_path = None
            path = decode_path(fields[index])
            index += 1
        records.append(
            {
                "status": status,
                "kind": kind,
                "path": path,
                "original_path": original_path,
            }
        )
    return records


def parse_porcelain_v1_z(raw: bytes) -> list[dict[str, str | None]]:
    """Parse NUL-delimited porcelain rows and consume rename/copy source paths."""

    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    records: list[dict[str, str | None]] = []
    index = 0
    while index < len(fields):
        row = fields[index]
        index += 1
        if len(row) < 3 or row[2:3] != b" ":
            raise ValueError(f"Git porcelain record is malformed: {decode_path(row)!r}")
        status = row[:2].decode("ascii", errors="strict")
        path = decode_path(row[3:])
        original_path = None
        if status[0] in {"R", "C"}:
            if index >= len(fields):
                raise ValueError(f"Git porcelain rename/copy record is truncated: {status!r}")
            original_path = decode_path(fields[index])
            index += 1
        records.append(
            {
                "status": status,
                "kind": status[0],
                "path": path,
                "original_path": original_path,
            }
        )
    return records


def affected_paths(record: dict[str, str | None]) -> list[str]:
    """Return paths mutated by one name-status record."""

    path = str(record["path"])
    original = record["original_path"]
    if record["kind"] == "R" and isinstance(original, str):
        return [original, path]
    return [path]


def staged_records(repo: Path) -> list[dict[str, str | None]]:
    """Return the complete staged name-status set."""

    raw = run_git(
        repo,
        "diff",
        "--cached",
        "--name-status",
        "-z",
        "--find-renames",
        "--find-copies",
    )
    return parse_name_status_z(raw)


def candidate_status(repo: Path, roots: list[str]) -> list[dict[str, str | None]]:
    """Return exact index/worktree status records for declared roots."""

    raw = run_git(
        repo,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--",
        *roots,
    )
    return parse_porcelain_v1_z(raw)


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
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def transition_count(repo: Path, precommit_oid: str | None) -> int:
    """Count commits after the recorded precommit boundary."""

    if precommit_oid is None:
        raw = run_git(repo, "rev-list", "--count", "HEAD")
    else:
        raw = run_git(repo, "rev-list", "--count", f"{precommit_oid}..HEAD")
    return int(raw.decode().strip())


def transition_records(
    repo: Path, precommit_oid: str | None
) -> list[dict[str, str | None]]:
    """Return path changes across the completed commit transition."""

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


def root_failures(repo: Path, roots: list[str]) -> list[str]:
    """Return roots that are missing, symlinked, or not directories."""

    return sorted(
        root for root in roots if (repo / root).is_symlink() or not (repo / root).is_dir()
    )


def remainder_records(repo: Path, roots: list[str]) -> list[dict[str, str | None]]:
    """Return untracked or worktree-divergent candidate status rows."""

    return [
        record
        for record in candidate_status(repo, roots)
        if record["status"] == "??" or str(record["status"])[1] != " "
    ]


def verify(repo: Path, manifest: dict[str, Any], phase: str) -> dict[str, Any]:
    """Verify the index, candidate remainder, or one-commit transition."""

    roots = manifest["candidate_roots"]
    precommit_oid = manifest["precommit_oid"]
    if phase == "postcommit":
        head = current_head(repo)
        if head is None:
            count = 0
            records: list[dict[str, str | None]] = []
        else:
            count = transition_count(repo, precommit_oid)
            records = transition_records(repo, precommit_oid)
        paths = [path for record in records for path in affected_paths(record)]
        outside = sorted(path for path in paths if not inside(path, roots))
        missing_coverage = sorted(root for root in roots if not any(inside(path, [root]) for path in paths))
        missing_roots = root_failures(repo, roots)
        remainder = remainder_records(repo, roots) if not missing_roots else []
        success = (
            count == 1
            and not outside
            and not missing_coverage
            and not missing_roots
            and not remainder
        )
        return {
            "status": "success" if success else "failure",
            "phase": phase,
            "condition": "exactly one commit contains every complete candidate root and no unrelated path",
            "expected": {
                "commit_count": 1,
                "outside": [],
                "missing_coverage": [],
                "missing_roots": [],
                "remainder": [],
            },
            "received": {
                "commit_count": count,
                "outside": outside,
                "missing_coverage": missing_coverage,
                "missing_roots": missing_roots,
                "remainder": remainder,
                "commit_oid": head,
            },
            "mode": MODE,
        }

    records = staged_records(repo)
    paths = [path for record in records for path in affected_paths(record)]
    outside = sorted(path for path in paths if not inside(path, roots))
    baseline_matches = current_head(repo) == precommit_oid
    if phase == "prestage":
        success = not outside and baseline_matches
        return {
            "status": "success" if success else "failure",
            "phase": phase,
            "condition": "the existing index has no unrelated path and HEAD matches precommit authority",
            "expected": {"outside": [], "precommit_oid": precommit_oid},
            "received": {"outside": outside, "precommit_oid": current_head(repo)},
            "mode": MODE,
        }

    missing_roots = root_failures(repo, roots)
    missing_coverage = sorted(root for root in roots if not any(inside(path, [root]) for path in paths))
    remainder = remainder_records(repo, roots) if not missing_roots else []
    success = (
        bool(records)
        and baseline_matches
        and not outside
        and not missing_roots
        and not missing_coverage
        and not remainder
    )
    return {
        "status": "success" if success else "failure",
        "phase": phase,
        "condition": "all physical roots are staged with no unrelated path or candidate remainder",
        "expected": {
            "outside": [],
            "missing_roots": [],
            "missing_coverage": [],
            "remainder": [],
            "precommit_oid": precommit_oid,
        },
        "received": {
            "outside": outside,
            "missing_roots": missing_roots,
            "missing_coverage": missing_coverage,
            "remainder": remainder,
            "precommit_oid": current_head(repo),
        },
        "staged_record_count": len(records),
        "mode": MODE,
    }


def write_candidate(repo: Path, root: str, text: str = "intent\n") -> Path:
    """Create one complete-root fixture file."""

    path = repo / root / "variant-001" / "intent.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def commit(repo: Path, message: str) -> None:
    """Create one fixture commit without invoking external hooks."""

    run_git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", message)


def self_test() -> dict[str, Any]:
    """Exercise positive and nearest-negative batch transitions."""

    assertions = 0
    with tempfile.TemporaryDirectory() as temporary:
        repo = Path(temporary)
        run_git(repo, "init", "--quiet", "--initial-branch=main")
        (repo / "baseline.txt").write_text("baseline\n", encoding="utf-8")
        run_git(repo, "add", "baseline.txt")
        commit(repo, "baseline")
        precommit_oid = current_head(repo)
        roots = [
            "review-pending-skills/pending-review/a",
            "review-pending-skills/pending-review/b",
        ]
        paths = [write_candidate(repo, root) for root in roots]
        manifest_path = repo / "manifest.json"
        manifest_path.write_text(
            json.dumps({"candidate_roots": roots, "precommit_oid": precommit_oid}),
            encoding="utf-8",
        )
        manifest = load_manifest(manifest_path)
        assert verify(repo, manifest, "prestage")["status"] == "success"
        assertions += 1

        (repo / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")
        run_git(repo, "add", "unrelated.txt")
        assert verify(repo, manifest, "prestage")["status"] == "failure"
        assertions += 1
        run_git(repo, "reset", "--", "unrelated.txt")
        (repo / "unrelated.txt").unlink()

        missing_manifest = {**manifest, "candidate_roots": [*roots, "review-pending-skills/pending-review/c"]}
        run_git(repo, "add", "--", *roots)
        assert verify(repo, missing_manifest, "poststage")["status"] == "failure"
        assertions += 1
        assert verify(repo, manifest, "poststage")["status"] == "success"
        assertions += 1

        paths[0].write_text("drift\n", encoding="utf-8")
        assert verify(repo, manifest, "poststage")["status"] == "failure"
        assertions += 1
        paths[0].write_text("intent\n", encoding="utf-8")
        assert verify(repo, manifest, "poststage")["status"] == "success"
        assertions += 1

        rename_copy = parse_name_status_z(
            b"R100\0old name\0new name\0C075\0source name\0copy name\0"
        )
        assert rename_copy == [
            {"status": "R100", "kind": "R", "path": "new name", "original_path": "old name"},
            {"status": "C075", "kind": "C", "path": "copy name", "original_path": "source name"},
        ]
        porcelain = parse_porcelain_v1_z(b"R  new name\0old name\0C  copy name\0source name\0")
        assert [record["original_path"] for record in porcelain] == ["old name", "source name"]
        assertions += 2

        commit(repo, "one batch")
        assert verify(repo, manifest, "postcommit")["status"] == "success"
        assertions += 1

        split_precommit = current_head(repo)
        split_manifest = {"candidate_roots": roots, "precommit_oid": split_precommit}
        paths[0].write_text("later-a\n", encoding="utf-8")
        run_git(repo, "add", "--", roots[0])
        commit(repo, "split a")
        paths[1].write_text("later-b\n", encoding="utf-8")
        run_git(repo, "add", "--", roots[1])
        commit(repo, "split b")
        split = verify(repo, split_manifest, "postcommit")
        assert split["status"] == "failure" and split["received"]["commit_count"] == 2
        assertions += 1

        malformed_path = repo / "malformed.json"
        malformed_path.write_text(
            json.dumps(
                {
                    "candidate_roots": ["review-pending-skills/pending-review/a/variant-001"],
                    "precommit_oid": split_precommit,
                }
            ),
            encoding="utf-8",
        )
        try:
            load_manifest(malformed_path)
        except ValueError:
            assertions += 1
        else:
            raise AssertionError("malformed candidate root was accepted")
    return {"status": "passed", "assertions": assertions, "mode": MODE}


def parse_args() -> argparse.Namespace:
    """Parse a manifest and verification phase or the self-test switch."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--phase", choices=("prestage", "poststage", "postcommit"))
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if not arguments.self_test and None in (arguments.repo, arguments.manifest, arguments.phase):
        parser.error("--repo, --manifest, and --phase are required unless --self-test is used")
    return arguments


def main() -> int:
    """Emit one machine-readable verification result."""

    arguments = parse_args()
    try:
        if arguments.self_test:
            output = self_test()
        else:
            output = verify(
                arguments.repo.expanduser().resolve(strict=True),
                load_manifest(arguments.manifest.expanduser()),
                arguments.phase,
            )
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        output = {
            "status": "failure",
            "phase": arguments.phase,
            "condition": "the creation-batch evidence is valid and inspectable",
            "expected": "valid manifest, repository, and Git status",
            "received": normalize_home_text(str(error)),
            "mode": MODE,
        }
        print(json.dumps(output, indent=2, sort_keys=True))
        return 2
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["status"] in {"success", "passed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
