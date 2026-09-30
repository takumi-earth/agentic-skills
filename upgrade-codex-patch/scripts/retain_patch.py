#!/usr/bin/env python3
"""Retain audited Codex patch bytes as an immutable skill resource."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile


class RetentionError(RuntimeError):
    def __init__(self, condition: str, expected: object, received: object):
        self.details = {
            "condition": condition,
            "expected": expected,
            "received": received,
        }
        super().__init__(condition)


def display(path: Path) -> str:
    expanded = path.expanduser().absolute()
    try:
        return "~/" + expanded.relative_to(Path.home()).as_posix()
    except ValueError:
        return str(expanded)


def retain_patch(source: Path, expected_sha256: str, skill_root: Path) -> dict:
    source = source.expanduser().absolute()
    expected_sha256 = expected_sha256.lower()
    if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
        raise RetentionError(
            "audited SHA-256 is valid", "64 hexadecimal digits", expected_sha256
        )
    if (
        re.fullmatch(r"codex-v\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?\.patch", source.name)
        is None
    ):
        raise RetentionError(
            "patch has a versioned resource name", "codex-v<release>.patch", source.name
        )
    data = source.read_bytes()
    actual_sha256 = hashlib.sha256(data).hexdigest()
    if actual_sha256 != expected_sha256:
        raise RetentionError(
            "source still matches audited bytes", expected_sha256, actual_sha256
        )
    skill_root = skill_root.expanduser().resolve(strict=True)
    if not (skill_root / "SKILL.md").is_file():
        raise RetentionError(
            "destination is a skill package", "root SKILL.md", display(skill_root)
        )
    resource_dir = skill_root / "assets" / "patches"
    if not resource_dir.resolve().is_relative_to(skill_root):
        raise RetentionError(
            "resource directory stays in the package",
            display(skill_root),
            display(resource_dir.resolve()),
        )
    destination = resource_dir / source.name
    result = {
        "schema_version": 1,
        "source": display(source),
        "resource": display(destination),
        "sha256": actual_sha256,
        "bytes": len(data),
    }
    if destination.exists() or destination.is_symlink():
        return confirm_existing(destination, data, result)
    resource_dir.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=resource_dir, prefix=".retain-patch-", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError:
            return confirm_existing(destination, data, result)
    finally:
        if temporary is not None:
            temporary.unlink()
    return {**result, "outcome": "retained", "writes": 1}


def confirm_existing(destination: Path, data: bytes, result: dict) -> dict:
    if destination.is_symlink() or not destination.is_file():
        raise RetentionError(
            "existing resource is a regular file", "regular file", display(destination)
        )
    existing = destination.read_bytes()
    if existing != data:
        raise RetentionError(
            "existing resource matches audited bytes",
            result["sha256"],
            hashlib.sha256(existing).hexdigest(),
        )
    return {**result, "outcome": "unchanged", "writes": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("patch", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument(
        "--skill-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    arguments = parser.parse_args()
    try:
        result = retain_patch(arguments.patch, arguments.sha256, arguments.skill_root)
    except RetentionError as error:
        result = {"schema_version": 1, "outcome": "failed", **error.details}
    except OSError as error:
        result = {
            "schema_version": 1,
            "outcome": "failed",
            "condition": "resource retention completes",
            "expected": "readable source and exclusively publishable resource",
            "received": str(error).replace(str(Path.home()), "~"),
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if result["outcome"] == "failed" else 0


if __name__ == "__main__":
    sys.exit(main())
