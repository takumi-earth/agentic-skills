#!/usr/bin/env python3
"""Shared deterministic I/O and validation helpers for rollout damage tooling."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


class AssessmentInputError(ValueError):
    """Report malformed, missing, or stale assessment input."""


def display_path(path: Path) -> str:
    """Render a path below the current home with a `~/` prefix."""
    resolved = path.expanduser().resolve(strict=False)
    home = Path.home().resolve(strict=False)
    try:
        return f"~/{resolved.relative_to(home)}"
    except ValueError:
        return str(resolved)


def resolve_path(value: str, base: Path) -> Path:
    """Resolve a manifest path from `~/`, absolute, or manifest-relative text."""
    if value == "~":
        return Path.home()
    if value.startswith("~/"):
        return Path.home() / value[2:]
    candidate = Path(value)
    return candidate if candidate.is_absolute() else base / candidate


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase SHA-256 digest for `data`."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """Hash one complete regular file."""
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> Any:
    """Load one JSON document with a path-qualified error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AssessmentInputError(f"cannot read JSON {display_path(path)}: {error}") from error


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load object-valued JSONL records with line-qualified errors."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise AssessmentInputError(f"cannot read JSONL {display_path(path)}: {error}") from error
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise AssessmentInputError(
                f"invalid JSONL at {display_path(path)}:{line_number}: {error}"
            ) from error
        if not isinstance(value, dict):
            raise AssessmentInputError(
                f"invalid JSONL at {display_path(path)}:{line_number}: expected object"
            )
        records.append(value)
    return records


def canonical_json(value: Any) -> str:
    """Serialize deterministic, human-readable JSON."""
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def atomic_write_text(path: Path, text: str) -> None:
    """Write text through an fsynced same-directory temporary file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def require_object(value: Any, location: str) -> dict[str, Any]:
    """Return `value` as an object or raise a located input error."""
    if not isinstance(value, dict):
        raise AssessmentInputError(f"{location}: expected object")
    return value


def require_list(value: Any, location: str) -> list[Any]:
    """Return `value` as a list or raise a located input error."""
    if not isinstance(value, list):
        raise AssessmentInputError(f"{location}: expected array")
    return value


def require_string(value: Any, location: str) -> str:
    """Return one nonempty string or raise a located input error."""
    if not isinstance(value, str) or not value.strip():
        raise AssessmentInputError(f"{location}: expected nonempty string")
    return value


def require_string_list(value: Any, location: str, *, allow_empty: bool = False) -> list[str]:
    """Validate an array of nonempty strings."""
    values = require_list(value, location)
    if not values and not allow_empty:
        raise AssessmentInputError(f"{location}: expected at least one item")
    return [require_string(item, f"{location}[{index}]") for index, item in enumerate(values)]


def require_exact_keys(value: dict[str, Any], required: set[str], optional: set[str], location: str) -> None:
    """Reject missing and unknown object keys."""
    keys = set(value)
    missing = sorted(required - keys)
    unknown = sorted(keys - required - optional)
    if missing:
        raise AssessmentInputError(f"{location}: missing keys {missing}")
    if unknown:
        raise AssessmentInputError(f"{location}: unknown keys {unknown}")


def require_unique(values: list[str], location: str) -> None:
    """Reject duplicate stable identifiers."""
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise AssessmentInputError(f"{location}: duplicate identifiers {duplicates}")
