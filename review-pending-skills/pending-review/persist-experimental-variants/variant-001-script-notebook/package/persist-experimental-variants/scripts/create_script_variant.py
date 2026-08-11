#!/usr/bin/env python3
"""Create one immutable script experiment with documented intent."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any


VARIANT_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
DIGEST_RE = re.compile(r"[0-9a-f]{64}\Z")
DEFAULT_NOTEBOOKS_RELATIVE = Path(".scratchpad/persist-experimental-variants")
VARIANT_ERROR_EXIT = 3


class VariantError(RuntimeError):
    """The requested source or variant destination is unsafe or invalid."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


def render_path(path: Path, home: Path | None = None) -> str:
    """Render paths beneath home with a portable tilde prefix."""

    resolved_path = path.expanduser().resolve(strict=False)
    resolved_home = (home or Path.home()).expanduser().resolve(strict=False)
    try:
        relative = resolved_path.relative_to(resolved_home)
    except ValueError:
        return str(resolved_path)
    if relative == Path("."):
        return "~"
    return f"~/{relative.as_posix()}"


def sha256_file(path: Path) -> str:
    """Hash one complete regular file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_canonical_repository(executing_path: Path | None = None) -> Path:
    """Resolve the canonical checkout from the real packaged-script location."""

    path = (executing_path or Path(__file__)).expanduser().resolve(strict=False)
    start = path if path.is_dir() else path.parent
    for candidate in (start, *start.parents):
        if (
            (candidate / ".git").exists()
            and (candidate / "AGENTS.md").is_file()
            and (candidate / "review-pending-skills" / "SKILL.md").is_file()
        ):
            return candidate.resolve()
    raise VariantError(
        "repository-unresolved",
        "cannot resolve the canonical Agentic Skills repository from the packaged script",
    )


def select_notebook_root(
    *,
    repository: Path,
    notebook_id: str | None,
    notebook_root: Path | None,
    external_deliverable: bool,
) -> Path:
    """Select a canonical scratch notebook or an explicitly authorized deliverable."""

    if notebook_id is not None and notebook_root is not None:
        raise VariantError(
            "notebook-selection-invalid",
            "provide either --notebook-id or --notebook-root, not both",
        )
    canonical_base = (repository / DEFAULT_NOTEBOOKS_RELATIVE).resolve(strict=False)
    if notebook_root is None:
        if external_deliverable:
            raise VariantError(
                "notebook-selection-invalid",
                "--external-deliverable requires --notebook-root",
            )
        if notebook_id is None or VARIANT_RE.fullmatch(notebook_id) is None:
            raise VariantError(
                "notebook-id-invalid",
                "default storage requires a lowercase hyphen-case --notebook-id",
            )
        return canonical_base / notebook_id

    selected = notebook_root.expanduser().resolve(strict=False)
    try:
        selected.relative_to(canonical_base)
        inside_canonical_scratch = True
    except ValueError:
        inside_canonical_scratch = False
    if not inside_canonical_scratch and not external_deliverable:
        raise VariantError(
            "external-destination-unauthorized",
            "an external --notebook-root requires the user-selected --external-deliverable assertion",
        )
    return selected


def require_predecessor(root: Path, predecessor_id: str) -> None:
    """Require one complete, identity-matching, byte-valid predecessor."""

    predecessor = root / predecessor_id
    if not predecessor.exists():
        raise VariantError(
            "predecessor-missing",
            f"predecessor does not exist: {predecessor_id}",
        )
    if predecessor.is_symlink() or not predecessor.is_dir():
        raise VariantError(
            "predecessor-malformed",
            f"predecessor must be a real directory: {predecessor_id}",
        )
    manifest_path = predecessor / "variant.json"
    intent_path = predecessor / "intent.md"
    if (
        manifest_path.is_symlink()
        or not manifest_path.is_file()
        or intent_path.is_symlink()
        or not intent_path.is_file()
    ):
        raise VariantError(
            "predecessor-malformed",
            f"predecessor lacks regular intent.md or variant.json metadata: {predecessor_id}",
        )
    try:
        manifest: Any = json.loads(manifest_path.read_text(encoding="utf-8"))
        intent_text = intent_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise VariantError(
            "predecessor-malformed",
            f"cannot read predecessor metadata for {predecessor_id}: {error}",
        ) from error
    if not isinstance(manifest, dict) or not intent_text.strip():
        raise VariantError(
            "predecessor-malformed",
            f"predecessor metadata is incomplete: {predecessor_id}",
        )
    if manifest.get("variant_id") != predecessor_id:
        raise VariantError(
            "predecessor-identity-mismatch",
            f"predecessor {predecessor_id} declares variant_id {manifest.get('variant_id')!r}",
        )
    declared_predecessors = manifest.get("predecessors")
    if not isinstance(declared_predecessors, list) or any(
        not isinstance(value, str) or VARIANT_RE.fullmatch(value) is None
        for value in declared_predecessors
    ):
        raise VariantError(
            "predecessor-malformed",
            f"predecessor has invalid predecessor metadata: {predecessor_id}",
        )
    if not isinstance(manifest.get("intent"), str) or not manifest["intent"].strip():
        raise VariantError(
            "predecessor-malformed",
            f"predecessor has an empty manifest intent: {predecessor_id}",
        )

    schema_version = manifest.get("schema_version")
    if schema_version == 1:
        source_name = manifest.get("source_name")
        payload_text = source_name
        digest = manifest.get("source_sha256")
    elif schema_version == 2:
        source_name = manifest.get("source_name")
        payload_text = manifest.get("payload_path")
        digest = manifest.get("payload_sha256")
    else:
        raise VariantError(
            "predecessor-malformed",
            f"predecessor has unsupported schema_version: {predecessor_id}",
        )
    if (
        not isinstance(source_name, str)
        or not source_name
        or Path(source_name).name != source_name
        or not isinstance(payload_text, str)
        or not payload_text
        or not isinstance(digest, str)
        or DIGEST_RE.fullmatch(digest) is None
    ):
        raise VariantError(
            "predecessor-malformed",
            f"predecessor has invalid payload metadata: {predecessor_id}",
        )
    payload_relative = Path(payload_text)
    if payload_relative.is_absolute() or ".." in payload_relative.parts:
        raise VariantError(
            "predecessor-malformed",
            f"predecessor payload path escapes its variant: {predecessor_id}",
        )
    if schema_version == 2 and payload_relative.parts != ("artifact", source_name):
        raise VariantError(
            "predecessor-malformed",
            f"predecessor payload is not artifact/<source-name>: {predecessor_id}",
        )
    payload = predecessor / payload_relative
    current = predecessor
    for part in payload_relative.parts:
        current /= part
        if current.is_symlink():
            raise VariantError(
                "predecessor-malformed",
                f"predecessor payload traverses a symlink: {predecessor_id}",
            )
    if not payload.is_file():
        raise VariantError(
            "predecessor-malformed",
            f"predecessor payload is missing: {predecessor_id}",
        )
    try:
        actual_digest = sha256_file(payload)
    except OSError as error:
        raise VariantError(
            "predecessor-malformed",
            f"cannot hash predecessor payload for {predecessor_id}: {error}",
        ) from error
    if actual_digest != digest:
        raise VariantError(
            "predecessor-malformed",
            f"predecessor payload digest does not match variant.json: {predecessor_id}",
        )


def validate_predecessors(root: Path, variant_id: str, predecessors: list[str]) -> None:
    """Reject invalid, self, duplicate, missing, or malformed predecessors."""

    if any(not isinstance(value, str) or VARIANT_RE.fullmatch(value) is None for value in predecessors):
        raise VariantError(
            "predecessor-id-invalid",
            "every predecessor must be a lowercase hyphen-case variant id",
        )
    duplicates = sorted({value for value in predecessors if predecessors.count(value) > 1})
    if duplicates:
        raise VariantError(
            "predecessor-duplicate",
            f"duplicate predecessor ids are forbidden: {duplicates}",
        )
    if variant_id in predecessors:
        raise VariantError(
            "predecessor-self",
            f"variant {variant_id!r} cannot name itself as a predecessor",
        )
    for predecessor_id in predecessors:
        require_predecessor(root, predecessor_id)


def _create_variant(
    *,
    source: Path,
    notebook_root: Path,
    variant_id: str,
    intent: str,
    predecessors: list[str],
) -> Path:
    """Implement variant creation after converting operational failures at the boundary."""

    raw_source = source.expanduser()
    if raw_source.is_symlink() or not raw_source.is_file():
        raise VariantError(
            "source-invalid",
            f"source must be a regular non-symlink file: {render_path(source)}",
        )
    source_path = raw_source.resolve()
    if VARIANT_RE.fullmatch(variant_id) is None:
        raise VariantError("variant-id-invalid", f"invalid variant id: {variant_id!r}")
    if not intent.strip():
        raise VariantError("intent-empty", "intent must not be empty")

    raw_root = notebook_root.expanduser()
    if raw_root.is_symlink() or (raw_root.exists() and not raw_root.is_dir()):
        raise VariantError(
            "notebook-root-invalid",
            f"notebook root must be a real directory: {render_path(raw_root)}",
        )
    raw_root.mkdir(parents=True, exist_ok=True)
    if raw_root.is_symlink() or not raw_root.is_dir():
        raise VariantError(
            "notebook-root-invalid",
            f"notebook root must be a real directory: {render_path(raw_root)}",
        )
    root = raw_root.resolve()
    validate_predecessors(root, variant_id, predecessors)

    target = root / variant_id
    claim = root / f".{variant_id}.claim"
    try:
        claim_descriptor = os.open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise VariantError(
            "variant-claimed",
            f"variant creation is already claimed: {variant_id}",
        ) from error
    temporary: Path | None = None
    try:
        if target.exists() or target.is_symlink():
            raise VariantError(
                "variant-exists",
                "variant already exists and will not be overwritten: "
                f"{render_path(target)}",
            )
        temporary = Path(tempfile.mkdtemp(prefix=f".{variant_id}.", dir=root))
        artifact = temporary / "artifact"
        artifact.mkdir()
        copied = artifact / source_path.name
        shutil.copyfile(source_path, copied)
        payload_relative = copied.relative_to(temporary).as_posix()
        manifest = {
            "intent": intent.strip(),
            "payload_path": payload_relative,
            "payload_sha256": sha256_file(copied),
            "predecessors": predecessors,
            "schema_version": 2,
            "source_name": source_path.name,
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
        return target
    finally:
        os.close(claim_descriptor)
        if temporary is not None and temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)
        try:
            claim.unlink(missing_ok=True)
        except OSError:
            pass


def create_variant(
    *,
    source: Path,
    notebook_root: Path,
    variant_id: str,
    intent: str,
    predecessors: list[str],
) -> Path:
    """Persist one never-overwritten single-file variant with stable failures."""

    try:
        return _create_variant(
            source=source,
            notebook_root=notebook_root,
            variant_id=variant_id,
            intent=intent,
            predecessors=predecessors,
        )
    except VariantError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise VariantError(
            "filesystem-failure",
            f"cannot create variant {variant_id!r}: {error}",
        ) from error


def parse_args() -> argparse.Namespace:
    """Parse one source, destination selection, identity, and intent."""

    parser = argparse.ArgumentParser(
        description="Copy one script into an immutable intent-documented variant."
    )
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--notebook-id")
    parser.add_argument("--notebook-root", type=Path)
    parser.add_argument("--external-deliverable", action="store_true")
    parser.add_argument("--variant-id", required=True)
    parser.add_argument("--intent", required=True)
    parser.add_argument("--predecessor", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    """Create the selected variant and print one human-readable result path."""

    arguments = parse_args()
    try:
        repository = resolve_canonical_repository()
        notebook_root = select_notebook_root(
            repository=repository,
            notebook_id=arguments.notebook_id,
            notebook_root=arguments.notebook_root,
            external_deliverable=arguments.external_deliverable,
        )
        output = create_variant(
            source=arguments.source,
            notebook_root=notebook_root,
            variant_id=arguments.variant_id,
            intent=arguments.intent,
            predecessors=arguments.predecessor,
        )
    except VariantError as error:
        print(f"VARIANT_ERROR[{error.code}]: {error}")
        return VARIANT_ERROR_EXIT
    print(render_path(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
