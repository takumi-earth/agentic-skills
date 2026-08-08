#!/usr/bin/env python3
"""Resolve one exact managed goal artifact with actionable diagnostics."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any


APPROACH = "environment-root"
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


def failure(code: str, condition: str, expected: Any, received: Any) -> dict[str, Any]:
    return {
        "status": "failure",
        "stage": "resolve-managed-goal-artifact",
        "code": code,
        "condition": condition,
        "expected": expected,
        "received": received,
        "artifact": None,
        "approach": APPROACH,
    }


def resolve_artifact(objective: str, codex_home: Path) -> dict[str, Any]:
    attachments = (codex_home.expanduser() / "attachments").resolve(strict=False)
    matches = [match.group("path") for match in WRAPPER.finditer(objective)]
    if len(matches) != 1:
        return failure(
            "objective-path-count",
            "objective contains exactly one managed pasted-text wrapper path",
            1,
            len(matches),
        )

    rendered = matches[0]
    candidate = Path(rendered).expanduser()
    if not candidate.is_absolute():
        return failure(
            "objective-path-not-absolute",
            "managed objective path is absolute or home-relative",
            "absolute path or ~/...",
            rendered,
        )
    resolved = candidate.resolve(strict=False)
    try:
        relative = resolved.relative_to(attachments)
    except ValueError:
        return failure(
            "attachments-root-mismatch",
            "resolved objective path remains beneath the configured attachments root",
            display(attachments),
            display(resolved),
        )
    if len(relative.parts) != 2 or UUID.fullmatch(relative.parts[0]) is None:
        return failure(
            "managed-path-shape",
            "managed path has attachments/<uuid>/<file> shape",
            "<uuid>/<file>",
            relative.as_posix(),
        )
    if not resolved.is_file():
        received = "missing" if not resolved.exists() else "not-regular-file"
        return failure(
            "artifact-not-file",
            "resolved managed artifact exists as a regular file",
            "regular-file",
            received,
        )
    return {
        "status": "success",
        "stage": "resolve-managed-goal-artifact",
        "code": "resolved-exact-artifact",
        "condition": "one exact regular managed file is named by the objective",
        "expected": {"attachments_root": display(attachments), "candidate_count": 1},
        "received": {"attachments_root": display(attachments), "candidate_count": 1},
        "artifact": display(resolved),
        "approach": APPROACH,
    }


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "codex"
        artifact = root / "attachments" / "12345678-1234-1234-1234-123456789abc" / "pasted-text-1.txt"
        artifact.parent.mkdir(parents=True)
        artifact.write_text("objective", encoding="utf-8")
        objective = f"pasted text file: {artifact}. Read this file before continuing."
        success = resolve_artifact(objective, root)
        wrong_root = resolve_artifact(objective, Path(temporary) / "wrong")
        assert success["status"] == "success", success
        assert success["artifact"] == str(artifact), success
        assert wrong_root["code"] == "attachments-root-mismatch", wrong_root
        assert wrong_root["expected"] != wrong_root["received"], wrong_root
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
    root = arguments.codex_home
    if root is None:
        root = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    result = resolve_artifact(arguments.objective, root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
