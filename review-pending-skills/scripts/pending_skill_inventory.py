#!/usr/bin/env python3
"""Inventory design-preserving pending skill variants without mutating them."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any


SCHEMA_VERSION = 1
NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PENDING_ROOT = PACKAGE_ROOT / "pending-review"


class InventoryError(RuntimeError):
    """A pending store entry is unsafe, incomplete, or inconsistent."""


def render_path(path: Path, home: Path | None = None) -> str:
    """Render paths beneath home with a portable tilde prefix."""

    resolved_path = path.expanduser().absolute()
    resolved_home = (home or Path.home()).expanduser().absolute()
    try:
        relative = resolved_path.relative_to(resolved_home)
    except ValueError:
        return str(resolved_path)
    if relative == Path("."):
        return "~"
    return f"~/{relative.as_posix()}"


def sha256_file(path: Path) -> str:
    """Hash one required variant file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def require_directory(path: Path, label: str) -> None:
    """Require one real directory rather than a symlink."""

    if path.is_symlink() or not path.is_dir():
        raise InventoryError(f"{label} is not a real directory: {render_path(path)}")


def require_file(path: Path, label: str) -> None:
    """Require one regular file rather than a symlink."""

    if path.is_symlink() or not path.is_file():
        raise InventoryError(f"{label} is not a regular file: {render_path(path)}")


def reject_tree_symlinks(root: Path) -> None:
    """Reject every symlink nested beneath one candidate root."""

    for directory, names, filenames in os.walk(root, followlinks=False):
        parent = Path(directory)
        for name in [*names, *filenames]:
            path = parent / name
            if path.is_symlink():
                raise InventoryError(
                    f"candidate contains a symlink: {render_path(path)}"
                )


def load_review(path: Path) -> dict[str, Any]:
    """Load one variant's structured review metadata."""

    require_file(path, "review metadata")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InventoryError(
            f"cannot read review metadata {render_path(path)}: {error}"
        ) from error
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise InventoryError(
            f"unsupported or malformed review metadata: {render_path(path)}"
        )
    return value


def validate_string_list(value: object, field: str, path: Path) -> list[str]:
    """Validate a review field containing strings."""

    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise InventoryError(
            f"review metadata field {field!r} is invalid: {render_path(path)}"
        )
    return value


def inventory_variant(candidate: Path, variant: Path) -> dict[str, Any]:
    """Validate and describe one design-preserving pending variant."""

    candidate_name = candidate.name
    variant_id = variant.name
    if NAME_RE.fullmatch(candidate_name) is None:
        raise InventoryError(f"invalid candidate name: {candidate_name!r}")
    if NAME_RE.fullmatch(variant_id) is None:
        raise InventoryError(f"invalid variant id: {variant_id!r}")
    require_directory(variant, "variant")

    review_path = variant / "review.json"
    intent_path = variant / "intent.md"
    package = variant / "package" / candidate_name
    skill_path = package / "SKILL.md"
    metadata_path = package / "agents" / "openai.yaml"

    review = load_review(review_path)
    require_file(intent_path, "variant intent")
    require_directory(variant / "package", "variant package root")
    require_directory(package, "candidate draft package")
    require_file(skill_path, "candidate SKILL.md")
    require_directory(package / "agents", "candidate agents directory")
    require_file(metadata_path, "candidate OpenAI metadata")

    if review.get("candidate_name") != candidate_name:
        raise InventoryError(
            f"candidate_name does not match directory: {render_path(review_path)}"
        )
    if review.get("variant_id") != variant_id:
        raise InventoryError(
            f"variant_id does not match directory: {render_path(review_path)}"
        )
    if review.get("status") != "pending":
        raise InventoryError(
            f"pending variant has non-pending status: {render_path(review_path)}"
        )

    predecessors = validate_string_list(review.get("predecessors"), "predecessors", review_path)
    provenance = validate_string_list(review.get("provenance"), "provenance", review_path)
    activation_effects = validate_string_list(
        review.get("activation_effects"), "activation_effects", review_path
    )
    relationships = review.get("relationships")
    if not isinstance(relationships, list) or any(
        not isinstance(item, dict) for item in relationships
    ):
        raise InventoryError(
            "review metadata field 'relationships' is invalid: "
            f"{render_path(review_path)}"
        )

    required_files = {
        "intent": intent_path,
        "review": review_path,
        "skill": skill_path,
        "openai_metadata": metadata_path,
    }
    return {
        "activation_effects": activation_effects,
        "candidate_name": candidate_name,
        "files": {
            name: {
                "path": str(path.relative_to(candidate.parents[1])),
                "sha256": sha256_file(path),
            }
            for name, path in required_files.items()
        },
        "predecessors": predecessors,
        "provenance": provenance,
        "relationships": relationships,
        "status": "pending",
        "variant_id": variant_id,
    }


def inventory_pending_store(pending_root: Path) -> dict[str, Any]:
    """Return a deterministic inventory of all candidate variants."""

    expanded_root = pending_root.expanduser()
    if expanded_root.is_symlink():
        raise InventoryError(
            f"pending-review root is not a real directory: {render_path(expanded_root)}"
        )
    root = expanded_root.resolve(strict=False)
    if not root.exists():
        return {
            "candidate_count": 0,
            "candidates": [],
            "pending_root": render_path(root),
            "schema_version": SCHEMA_VERSION,
            "variant_count": 0,
        }
    require_directory(root, "pending-review root")

    candidates: list[dict[str, Any]] = []
    variant_count = 0
    for candidate in sorted(root.iterdir(), key=lambda path: path.name):
        require_directory(candidate, "candidate")
        reject_tree_symlinks(candidate)
        variants = [
            inventory_variant(candidate, variant)
            for variant in sorted(candidate.iterdir(), key=lambda path: path.name)
        ]
        if not variants:
            raise InventoryError(
                f"candidate has no variants: {render_path(candidate)}"
            )
        variant_count += len(variants)
        candidates.append({"name": candidate.name, "variants": variants})

    return {
        "candidate_count": len(candidates),
        "candidates": candidates,
        "pending_root": render_path(root),
        "schema_version": SCHEMA_VERSION,
        "variant_count": variant_count,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory design-preserving pending skill variants as JSON."
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_PENDING_ROOT)
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    try:
        report = inventory_pending_store(arguments.root)
    except (InventoryError, OSError) as error:
        print(f"INVENTORY_ERROR: {error}", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
