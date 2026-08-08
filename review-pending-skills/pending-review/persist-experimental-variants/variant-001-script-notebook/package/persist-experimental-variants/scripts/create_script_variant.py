#!/usr/bin/env python3
"""Create one immutable script experiment with documented intent."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile


VARIANT_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


class VariantError(RuntimeError):
    """The requested source or variant destination is unsafe or invalid."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def create_variant(
    *,
    source: Path,
    notebook_root: Path,
    variant_id: str,
    intent: str,
    predecessors: list[str],
) -> Path:
    """Atomically persist one never-overwritten script variant."""

    raw_source = source.expanduser()
    if raw_source.is_symlink() or not raw_source.is_file():
        raise VariantError(f"source must be a regular non-symlink file: {source}")
    source_path = raw_source.resolve()
    if VARIANT_RE.fullmatch(variant_id) is None:
        raise VariantError(f"invalid variant id: {variant_id!r}")
    if not intent.strip():
        raise VariantError("intent must not be empty")
    if any(VARIANT_RE.fullmatch(value) is None for value in predecessors):
        raise VariantError("every predecessor must be a lowercase hyphen-case variant id")

    raw_root = notebook_root.expanduser()
    if raw_root.is_symlink():
        raise VariantError(f"notebook root must be a real directory: {raw_root}")
    raw_root.mkdir(parents=True, exist_ok=True)
    if raw_root.is_symlink() or not raw_root.is_dir():
        raise VariantError(f"notebook root must be a real directory: {raw_root}")
    root = raw_root.resolve()
    target = root / variant_id
    if target.exists() or target.is_symlink():
        raise VariantError(f"variant already exists and will not be overwritten: {target}")

    temporary = Path(tempfile.mkdtemp(prefix=f".{variant_id}.", dir=root))
    try:
        copied = temporary / source_path.name
        shutil.copyfile(source_path, copied)
        manifest = {
            "intent": intent.strip(),
            "predecessors": predecessors,
            "schema_version": 1,
            "source_name": source_path.name,
            "source_sha256": sha256_file(copied),
            "variant_id": variant_id,
        }
        (temporary / "intent.md").write_text(
            f"# {variant_id}\n\n{intent.strip()}\n",
            encoding="utf-8",
        )
        (temporary / "variant.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.rename(target)
    except (OSError, ValueError) as error:
        shutil.rmtree(temporary, ignore_errors=True)
        raise VariantError(f"cannot create variant {variant_id!r}: {error}") from error
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy one script into an immutable intent-documented variant."
    )
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--notebook-root", type=Path, required=True)
    parser.add_argument("--variant-id", required=True)
    parser.add_argument("--intent", required=True)
    parser.add_argument("--predecessor", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    try:
        output = create_variant(
            source=arguments.source,
            notebook_root=arguments.notebook_root,
            variant_id=arguments.variant_id,
            intent=arguments.intent,
            predecessors=arguments.predecessor,
        )
    except VariantError as error:
        print(f"VARIANT_ERROR: {error}")
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
