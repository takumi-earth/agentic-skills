#!/usr/bin/env python3
"""Verify a write-ahead candidate-root manifest against one staged Git batch."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
from typing import Any


MODE = "write-ahead-batch-manifest"


def run_git(repo: Path, *arguments: str) -> bytes:
    completed = subprocess.run(["git", *arguments], cwd=repo, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"git command failed; condition=exit code 0; expected=0; received={completed.returncode}; argv={arguments!r}; stderr={completed.stderr.decode(errors='replace')!r}"
        )
    return completed.stdout


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file() and not item.is_symlink()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    roots = value.get("candidate_roots") if isinstance(value, dict) else None
    hashes = value.get("tree_hashes") if isinstance(value, dict) else None
    if not isinstance(roots, list) or not roots or not isinstance(hashes, dict):
        raise ValueError("manifest shape check failed; expected candidate_roots and tree_hashes")
    for root in roots:
        parsed = PurePosixPath(root)
        if not isinstance(root, str) or parsed.is_absolute() or ".." in parsed.parts:
            raise ValueError(f"candidate root check failed; received={root!r}")
        if not isinstance(hashes.get(root), str):
            raise ValueError(f"tree hash check failed; expected hash for={root!r}; received={hashes.get(root)!r}")
    return value


def verify(repo: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    roots = sorted(manifest["candidate_roots"])
    staged_raw = run_git(repo, "diff", "--cached", "--name-only", "-z")
    staged = sorted(item.decode() for item in staged_raw.split(b"\0") if item)
    outside = sorted(path for path in staged if not any(path == root or path.startswith(f"{root}/") for root in roots))
    received_hashes = {root: tree_hash(repo / root) for root in roots}
    missing = sorted(root for root in roots if not any(path.startswith(f"{root}/") or path == root for path in staged))
    if outside or missing or received_hashes != manifest["tree_hashes"]:
        return {
            "status": "failure",
            "condition": "staged root set and current tree hashes equal the write-ahead manifest",
            "expected": {"outside": [], "missing": [], "tree_hashes": manifest["tree_hashes"]},
            "received": {"outside": outside, "missing": missing, "tree_hashes": received_hashes},
            "mode": MODE,
        }
    return {
        "status": "success",
        "condition": "staged root set and current tree hashes equal the write-ahead manifest",
        "expected": {"outside": [], "missing": [], "tree_hashes": manifest["tree_hashes"]},
        "received": {"outside": [], "missing": [], "tree_hashes": received_hashes},
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
        hashes = {root: tree_hash(repo / root) for root in roots}
        manifest = {"candidate_roots": roots, "tree_hashes": hashes}
        run_git(repo, "add", "--", *roots)
        success = verify(repo, manifest)
        (repo / roots[0] / "variant-001" / "intent.md").write_text("drift\n", encoding="utf-8")
        drift = verify(repo, manifest)
        assert success["status"] == "success", success
        assert drift["status"] == "failure", drift
        assert drift["expected"]["tree_hashes"] != drift["received"]["tree_hashes"], drift
        assert drift["condition"].startswith("staged root set"), drift
    return {"status": "passed", "assertions": 4, "mode": MODE}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if not arguments.self_test and (arguments.repo is None or arguments.manifest is None):
        parser.error("--repo and --manifest are required unless --self-test is used")
    return arguments


def main() -> int:
    arguments = parse_args()
    if arguments.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return 0
    output = verify(arguments.repo.expanduser().resolve(strict=True), load_manifest(arguments.manifest.expanduser()))
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
