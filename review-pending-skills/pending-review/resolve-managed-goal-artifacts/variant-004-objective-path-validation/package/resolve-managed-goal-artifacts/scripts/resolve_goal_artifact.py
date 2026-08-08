#!/usr/bin/env python3
"""Resolve and validate the exact managed path embedded in objective prose."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any


APPROACH = "objective-path-validation"
HOME = Path.home().resolve()
WRAPPER = re.compile(
    r"pasted text file:\s*(?P<path>.+?)\. Read this file before continuing\.?"
)
UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\Z")


def display(path: Path) -> str:
    absolute = path.expanduser().absolute()
    try:
        relative = absolute.relative_to(HOME)
    except ValueError:
        return str(absolute)
    return "~" if relative == Path(".") else f"~/{relative.as_posix()}"


def result(status: str, code: str, condition: str, expected: Any, received: Any, artifact: str | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "stage": "validate-objective-managed-path",
        "code": code,
        "condition": condition,
        "expected": expected,
        "received": received,
        "artifact": artifact,
        "approach": APPROACH,
    }


def resolve_artifact(objective: str, configured_home: Path) -> dict[str, Any]:
    matches = [match.group("path") for match in WRAPPER.finditer(objective)]
    if len(matches) != 1:
        return result("failure", "objective-path-count", "exactly one pasted-text path is present", 1, len(matches))
    candidate = Path(matches[0]).expanduser()
    if not candidate.is_absolute():
        return result("failure", "path-not-absolute", "objective path is absolute or home-relative", "absolute path or ~/...", matches[0])
    resolved = candidate.resolve(strict=False)
    configured_attachments = (configured_home.expanduser() / "attachments").resolve(strict=False)
    parts = resolved.parts
    try:
        index = len(parts) - 1 - tuple(reversed(parts)).index("attachments")
    except ValueError:
        return result("failure", "missing-attachments-segment", "path contains an attachments segment", ".../attachments/<uuid>/<file>", display(resolved))
    inferred_attachments = Path(*parts[: index + 1])
    suffix = parts[index + 1 :]
    if len(suffix) != 2 or UUID.fullmatch(suffix[0]) is None:
        return result("failure", "managed-path-shape", "path has attachments/<uuid>/<file> shape", "<uuid>/<file>", "/".join(suffix))
    if inferred_attachments != configured_attachments:
        return result("failure", "attachments-root-mismatch", "objective-inferred attachments root equals configured attachments root", display(configured_attachments), display(inferred_attachments))
    if not resolved.is_file():
        received = "missing" if not resolved.exists() else "not-regular-file"
        return result("failure", "artifact-not-file", "objective path resolves to a regular file", "regular-file", received)
    return result("success", "validated-objective-path", "one exact managed path matches the configured root", display(configured_attachments), display(inferred_attachments), display(resolved))


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "codex"
        artifact = root / "attachments" / "12345678-1234-1234-1234-123456789abc" / "pasted text 1.txt"
        artifact.parent.mkdir(parents=True)
        artifact.write_text("objective", encoding="utf-8")
        objective = f"pasted text file: {artifact}. Read this file before continuing."
        success = resolve_artifact(objective, root)
        mismatch = resolve_artifact(objective, Path(temporary) / "other")
        duplicate = resolve_artifact(f"{objective} {objective}", root)
        assert success["status"] == "success", success
        assert mismatch["code"] == "attachments-root-mismatch", mismatch
        assert mismatch["expected"] != mismatch["received"], mismatch
        assert duplicate["received"] == 2, duplicate
    return {"status": "passed", "assertions": 4, "approach": APPROACH}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--objective")
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if not arguments.self_test and arguments.objective is None:
        parser.error("--objective is required unless --self-test is used")
    return arguments


def main() -> int:
    arguments = parse_args()
    if arguments.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return 0
    root = arguments.codex_home or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    outcome = resolve_artifact(arguments.objective, root)
    print(json.dumps(outcome, indent=2, sort_keys=True))
    return 0 if outcome["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
