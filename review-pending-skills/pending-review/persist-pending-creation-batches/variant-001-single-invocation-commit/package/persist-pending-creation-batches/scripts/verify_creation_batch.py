#!/usr/bin/env python3
"""Verify a complete pending-candidate Git batch before one commit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
from typing import Any


MODE = "single-invocation-commit"


def run_git(repo: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"git command failed; condition=exit code 0; expected=0; received={completed.returncode}; "
            f"argv={arguments!r}; stderr={completed.stderr.decode(errors='replace')!r}"
        )
    return completed.stdout


def load_roots(manifest: Path) -> list[str]:
    value = json.loads(manifest.read_text(encoding="utf-8"))
    roots = value.get("candidate_roots") if isinstance(value, dict) else None
    if not isinstance(roots, list) or not roots or any(not isinstance(item, str) for item in roots):
        raise ValueError("candidate root check failed; expected=nonempty string list; received=invalid")
    normalized: list[str] = []
    for root in roots:
        path = PurePosixPath(root)
        if path.is_absolute() or ".." in path.parts or len(path.parts) < 3:
            raise ValueError(f"candidate root path check failed; expected=repository-relative candidate root; received={root!r}")
        normalized.append(path.as_posix().rstrip("/"))
    if len(set(normalized)) != len(normalized):
        raise ValueError("candidate root uniqueness check failed; expected=unique; received=duplicates")
    return sorted(normalized)


def inside(path: str, roots: list[str]) -> bool:
    return any(path == root or path.startswith(f"{root}/") for root in roots)


def staged_names(repo: Path) -> list[str]:
    raw = run_git(repo, "diff", "--cached", "--name-only", "-z")
    return sorted(item.decode() for item in raw.split(b"\0") if item)


def candidate_status(repo: Path, roots: list[str]) -> list[str]:
    raw = run_git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", *roots)
    return [item.decode(errors="replace") for item in raw.split(b"\0") if item]


def verify(repo: Path, roots: list[str], phase: str) -> dict[str, Any]:
    staged = staged_names(repo)
    outside = sorted(path for path in staged if not inside(path, roots))
    if outside:
        return {
            "status": "failure",
            "phase": phase,
            "condition": "every staged path belongs to the declared candidate-root set",
            "expected": roots,
            "received": outside,
            "mode": MODE,
        }
    if phase == "prestage":
        return {
            "status": "success",
            "phase": phase,
            "condition": "the existing index contains no path outside the declared candidate-root set",
            "expected": [],
            "received": outside,
            "mode": MODE,
        }
    missing_roots = sorted(root for root in roots if not any(inside(path, [root]) for path in staged))
    status_rows = candidate_status(repo, roots)
    remainder = sorted(
        row for row in status_rows if row.startswith("??") or (len(row) >= 2 and row[1] != " ")
    )
    if not staged or missing_roots or remainder:
        return {
            "status": "failure",
            "phase": phase,
            "condition": "all roots are staged and no untracked or unstaged candidate change remains",
            "expected": {"missing_roots": [], "remainder": []},
            "received": {"missing_roots": missing_roots, "remainder": remainder},
            "mode": MODE,
        }
    return {
        "status": "success",
        "phase": phase,
        "condition": "all complete candidate roots form one clean staged batch",
        "expected": {"candidate_roots": roots, "remainder": []},
        "received": {"candidate_roots": roots, "remainder": []},
        "staged_count": len(staged),
        "mode": MODE,
    }


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temporary:
        repo = Path(temporary)
        run_git(repo, "init", "--quiet")
        roots = ["review-pending-skills/pending-review/a", "review-pending-skills/pending-review/b"]
        for root in roots:
            path = repo / root / "variant-001" / "intent.md"
            path.parent.mkdir(parents=True)
            path.write_text("intent\n", encoding="utf-8")
        manifest = repo / "manifest.json"
        manifest.write_text(json.dumps({"candidate_roots": roots}), encoding="utf-8")
        before = verify(repo, load_roots(manifest), "prestage")
        run_git(repo, "add", "--", *roots)
        after = verify(repo, load_roots(manifest), "poststage")
        assert before["status"] == "success", before
        assert after["status"] == "success", after
        assert after["staged_count"] == 2, after
        assert after["received"]["remainder"] == [], after
    return {"status": "passed", "assertions": 4, "mode": MODE}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--phase", choices=("prestage", "poststage"))
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if not arguments.self_test and None in (arguments.repo, arguments.manifest, arguments.phase):
        parser.error("--repo, --manifest, and --phase are required unless --self-test is used")
    return arguments


def main() -> int:
    arguments = parse_args()
    if arguments.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return 0
    output = verify(arguments.repo.expanduser().resolve(strict=True), load_roots(arguments.manifest.expanduser()), arguments.phase)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
