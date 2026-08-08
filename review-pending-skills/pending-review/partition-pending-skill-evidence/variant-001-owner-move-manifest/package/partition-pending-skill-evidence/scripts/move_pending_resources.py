#!/usr/bin/env python3
"""Validate and execute an ownership-preserving pending-resource move manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any


HOME = Path.home().resolve()


def display(path: Path) -> str:
    absolute = path.expanduser().absolute()
    try:
        relative = absolute.relative_to(HOME)
    except ValueError:
        return str(absolute)
    return "~" if relative == Path(".") else f"~/{relative.as_posix()}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def contained(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("manifest schema check failed; expected schema_version=1")
    moves = value.get("moves")
    if not isinstance(moves, list) or not moves:
        raise ValueError("manifest move check failed; expected one or more move records")
    return value


def validate(repo: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    repository = repo.expanduser().resolve(strict=True)
    scratch = (repository / ".scratchpad").resolve(strict=True)
    pending = (repository / "review-pending-skills" / "pending-review").resolve(strict=True)
    seen_sources: set[Path] = set()
    seen_destinations: set[Path] = set()
    checked: list[dict[str, Any]] = []
    for index, record in enumerate(manifest["moves"]):
        if not isinstance(record, dict):
            raise ValueError(f"move record {index} must be an object")
        if record.get("classification") != "reusable-resource":
            raise ValueError(
                f"move record {index} classification check failed; "
                f"expected='reusable-resource'; received={record.get('classification')!r}"
            )
        source = Path(record.get("source", "")).expanduser().resolve(strict=False)
        destination = Path(record.get("destination", "")).expanduser().resolve(strict=False)
        expected_hash = record.get("sha256")
        if source in seen_sources or destination in seen_destinations:
            raise ValueError(f"move ownership uniqueness check failed at record {index}")
        seen_sources.add(source)
        seen_destinations.add(destination)
        if not contained(source, scratch):
            raise ValueError(
                f"source containment check failed; expected beneath={display(scratch)}; received={display(source)}"
            )
        if not contained(destination, pending):
            raise ValueError(
                f"destination containment check failed; expected beneath={display(pending)}; received={display(destination)}"
            )
        if source.is_symlink() or not source.is_file():
            received = "symlink" if source.is_symlink() else "missing-or-not-file"
            raise ValueError(
                f"source type check failed; expected=regular-file; received={received}; source={display(source)}"
            )
        if destination.exists() or destination.is_symlink():
            raise ValueError(
                f"destination absence check failed; expected=absent; received=present; destination={display(destination)}"
            )
        if not destination.parent.is_dir() or destination.parent.is_symlink():
            raise ValueError(
                f"destination parent check failed; expected=existing-real-directory; received={display(destination.parent)}"
            )
        received_hash = sha256(source)
        if not isinstance(expected_hash, str) or received_hash != expected_hash:
            raise ValueError(
                f"source hash check failed; expected={expected_hash!r}; received={received_hash!r}; source={display(source)}"
            )
        checked.append(
            {
                "source": display(source),
                "destination": display(destination),
                "sha256": received_hash,
                "classification": "reusable-resource",
            }
        )
    return checked


def execute(checked: list[dict[str, Any]]) -> list[dict[str, Any]]:
    moved: list[dict[str, Any]] = []
    for record in checked:
        source = Path(record["source"]).expanduser()
        destination = Path(record["destination"]).expanduser()
        completed = subprocess.run(
            ["mv", "--", str(source), str(destination)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"mv failed; condition=exit code 0; expected=0; received={completed.returncode}; "
                f"source={record['source']}; destination={record['destination']}; stderr={completed.stderr.strip()!r}"
            )
        if source.exists() or source.is_symlink():
            raise RuntimeError(
                f"source removal check failed after mv; expected=absent; received=present; source={record['source']}"
            )
        if not destination.is_file() or sha256(destination) != record["sha256"]:
            received = sha256(destination) if destination.is_file() else "missing-or-not-file"
            raise RuntimeError(
                f"destination integrity check failed; expected={record['sha256']}; received={received}; destination={record['destination']}"
            )
        moved.append(record)
    return moved


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temporary:
        repo = Path(temporary) / "repo"
        source = repo / ".scratchpad" / "run" / "resource.py"
        destination = (
            repo
            / "review-pending-skills"
            / "pending-review"
            / "candidate"
            / "variant-001"
            / "package"
            / "candidate"
            / "scripts"
            / "resource.py"
        )
        source.parent.mkdir(parents=True)
        destination.parent.mkdir(parents=True)
        source.write_text("resource\n", encoding="utf-8")
        manifest = {
            "schema_version": 1,
            "moves": [
                {
                    "source": str(source),
                    "destination": str(destination),
                    "sha256": sha256(source),
                    "classification": "reusable-resource",
                }
            ],
        }
        checked = validate(repo, manifest)
        moved = execute(checked)
        assert len(moved) == 1
        assert not source.exists()
        assert destination.read_text(encoding="utf-8") == "resource\n"
        assert sha256(destination) == moved[0]["sha256"]
    return {"status": "passed", "assertions": 4, "operation": "mv"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--manifest", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--execute", action="store_true")
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
    checked = validate(arguments.repo, load_manifest(arguments.manifest))
    moved = execute(checked) if arguments.execute else []
    print(
        json.dumps(
            {
                "status": "moved" if arguments.execute else "validated",
                "checked": checked,
                "moved": moved,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
