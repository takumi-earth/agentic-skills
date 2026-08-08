#!/usr/bin/env python3
"""Snapshot and verify the filesystem scope of approved skill changes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = 1
SKILL_NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


class GuardError(Exception):
    """A typed input, scope, snapshot, or filesystem validation failure."""


def path_exists(path: Path) -> bool:
    """Return whether a path exists without following a final symlink."""

    return os.path.lexists(path)


def is_within(path: Path, root: Path) -> bool:
    """Return whether `path` is contained by `root`."""

    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def validate_skill_name(name: str) -> str:
    """Validate one direct user-level skill directory name."""

    if name == ".system" or SKILL_NAME_RE.fullmatch(name) is None:
        raise GuardError(
            f"invalid user-level skill name {name!r}; expected lowercase hyphen-case"
        )
    return name


def resolve_skills_root(raw: Path) -> Path:
    """Resolve and validate the user-owned skills root."""

    root = raw.expanduser().resolve()
    if not root.is_dir():
        raise GuardError(f"skills root is not a directory: {root}")
    return root


def resolve_package(root: Path, name: str) -> Path:
    """Resolve a validated direct child of the skills root."""

    validated = validate_skill_name(name)
    package = root / validated
    if package.parent != root:
        raise GuardError(f"skill package escapes skills root: {name!r}")
    return package


def sha256_file(path: Path) -> str:
    """Hash a regular file without loading it completely into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def validate_symlink(package: Path, path: Path, target: str) -> None:
    """Reject a symlink whose lexical target resolves outside its package."""

    target_path = Path(target)
    resolved = (
        target_path.resolve(strict=False)
        if target_path.is_absolute()
        else (path.parent / target_path).resolve(strict=False)
    )
    package_root = package.resolve()
    if not is_within(resolved, package_root):
        relative = path.relative_to(package).as_posix()
        raise GuardError(
            f"symlink escapes skill package: {package.name}/{relative} -> {target}"
        )


def scan_package(package: Path) -> list[dict[str, str]]:
    """Return deterministic file, directory, and symlink facts for one package."""

    if package.is_symlink() or not package.is_dir():
        raise GuardError(f"skill package is not a real directory: {package}")

    entries: list[dict[str, str]] = []
    pending = [package]
    while pending:
        directory = pending.pop()
        try:
            children = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as error:
            raise GuardError(f"cannot scan skill package directory {directory}: {error}") from error
        for child in children:
            path = Path(child.path)
            relative = path.relative_to(package).as_posix()
            try:
                if child.is_symlink():
                    target = os.readlink(path)
                    validate_symlink(package, path, target)
                    entries.append(
                        {"kind": "symlink", "path": relative, "target": target}
                    )
                elif child.is_dir(follow_symlinks=False):
                    entries.append({"kind": "directory", "path": relative})
                    pending.append(path)
                elif child.is_file(follow_symlinks=False):
                    entries.append(
                        {
                            "kind": "file",
                            "path": relative,
                            "sha256": sha256_file(path),
                        }
                    )
                else:
                    raise GuardError(
                        f"unsupported filesystem entry in skill package: {package.name}/{relative}"
                    )
            except OSError as error:
                raise GuardError(
                    f"cannot inspect skill package entry {package.name}/{relative}: {error}"
                ) from error

    return sorted(entries, key=lambda entry: (entry["path"], entry["kind"]))


def target_snapshot(root: Path, name: str, mode: str) -> dict[str, Any]:
    """Build one validated existing- or new-package snapshot entry."""

    package = resolve_package(root, name)
    exists = path_exists(package)
    if mode == "existing":
        if not exists:
            raise GuardError(f"expected existing skill package is missing: {package}")
        return {
            "entries": scan_package(package),
            "mode": mode,
            "name": name,
            "state": "present",
        }
    if mode == "new":
        if exists:
            raise GuardError(f"expected new skill package already exists: {package}")
        return {"entries": [], "mode": mode, "name": name, "state": "absent"}
    raise GuardError(f"unsupported target mode: {mode!r}")


def write_manifest(path: Path, manifest: dict[str, Any], skills_root: Path) -> None:
    """Atomically write one deterministic manifest outside the skills root."""

    output = path.expanduser().resolve(strict=False)
    if is_within(output, skills_root):
        raise GuardError(f"snapshot output must be outside the skills root: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            json.dump(manifest, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, output)
        temporary_name = None
    except OSError as error:
        raise GuardError(f"cannot write snapshot manifest {output}: {error}") from error
    finally:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink()
            except FileNotFoundError:
                pass


def create_snapshot(
    skills_root: Path,
    existing: list[str],
    new: list[str],
    output: Path,
) -> dict[str, Any]:
    """Create and write one approved-target baseline manifest."""

    root = resolve_skills_root(skills_root)
    duplicates = sorted(set(existing) & set(new))
    if duplicates:
        raise GuardError(
            "skill targets cannot be both existing and new: " + ", ".join(duplicates)
        )
    if not existing and not new:
        raise GuardError("snapshot requires at least one --existing or --new target")

    targets = [target_snapshot(root, name, "existing") for name in sorted(set(existing))]
    targets.extend(target_snapshot(root, name, "new") for name in sorted(set(new)))
    targets.sort(key=lambda target: target["name"])
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "skills_root": str(root),
        "targets": targets,
    }
    write_manifest(output, manifest, root)
    return manifest


def load_manifest(path: Path) -> dict[str, Any]:
    """Load and structurally validate a scope-guard manifest."""

    source = path.expanduser().resolve()
    try:
        with source.open(encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        raise GuardError(f"cannot read snapshot manifest {source}: {error}") from error
    if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION:
        raise GuardError(f"unsupported or malformed snapshot manifest: {source}")
    root_value = manifest.get("skills_root")
    targets = manifest.get("targets")
    if not isinstance(root_value, str) or not isinstance(targets, list) or not targets:
        raise GuardError(f"snapshot manifest lacks skills_root or targets: {source}")

    root = resolve_skills_root(Path(root_value))
    names: set[str] = set()
    for target in targets:
        if not isinstance(target, dict):
            raise GuardError(f"snapshot manifest contains a malformed target: {source}")
        name = target.get("name")
        mode = target.get("mode")
        state = target.get("state")
        entries = target.get("entries")
        if not isinstance(name, str) or mode not in {"existing", "new"}:
            raise GuardError(f"snapshot manifest contains an invalid target: {source}")
        validate_skill_name(name)
        if name in names:
            raise GuardError(f"snapshot manifest repeats target {name!r}: {source}")
        names.add(name)
        expected_state = "present" if mode == "existing" else "absent"
        if state != expected_state or not isinstance(entries, list):
            raise GuardError(f"snapshot target has inconsistent state: {name}")
        for entry in entries:
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("path"), str)
                or entry.get("kind") not in {"directory", "file", "symlink"}
            ):
                raise GuardError(f"snapshot target has malformed entries: {name}")
    manifest["skills_root"] = str(root)
    return manifest


def entry_map(entries: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    """Index snapshot entries by package-relative path."""

    return {entry["path"]: entry for entry in entries}


def diff_entries(
    expected: list[dict[str, str]], actual: list[dict[str, str]]
) -> dict[str, list[str]]:
    """Return added, modified, and removed package-relative paths."""

    before = entry_map(expected)
    after = entry_map(actual)
    before_paths = set(before)
    after_paths = set(after)
    return {
        "added": sorted(after_paths - before_paths),
        "modified": sorted(
            path for path in before_paths & after_paths if before[path] != after[path]
        ),
        "removed": sorted(before_paths - after_paths),
    }


def scan_target_state(root: Path, target: dict[str, Any]) -> dict[str, Any]:
    """Read current state for one manifest target."""

    name = target["name"]
    package = resolve_package(root, name)
    if not path_exists(package):
        return {"entries": [], "state": "absent"}
    return {"entries": scan_package(package), "state": "present"}


def check_unchanged(snapshot: Path) -> tuple[bool, dict[str, Any]]:
    """Check that all targeted package baselines remain unchanged."""

    manifest = load_manifest(snapshot)
    root = Path(manifest["skills_root"])
    changes: list[dict[str, Any]] = []
    for target in manifest["targets"]:
        current = scan_target_state(root, target)
        if current["state"] == target["state"] and current["entries"] == target["entries"]:
            continue
        changes.append(
            {
                "diff": diff_entries(target["entries"], current["entries"]),
                "expected_state": target["state"],
                "name": target["name"],
                "state": current["state"],
            }
        )
    report = {
        "changes": changes,
        "status": "unchanged" if not changes else "changed",
    }
    return not changes, report


def validate_allowed_path(value: str, target_names: set[str]) -> str:
    """Validate one skills-root-relative allowlist path."""

    path = PurePosixPath(value)
    if path.is_absolute() or len(path.parts) < 2 or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        raise GuardError(f"invalid allowlisted path: {value!r}")
    if path.parts[0] not in target_names:
        raise GuardError(f"allowlisted path is outside targeted skills: {value!r}")
    return path.as_posix()


def directory_change_allowed(path: str, allowed: set[str]) -> bool:
    """Allow a directory change only when it contains an allowlisted path."""

    prefix = f"{path}/"
    return path in allowed or any(item.startswith(prefix) for item in allowed)


def verify_snapshot(snapshot: Path, allow: list[str]) -> tuple[bool, dict[str, Any]]:
    """Verify that only allowlisted paths changed in targeted packages."""

    manifest = load_manifest(snapshot)
    root = Path(manifest["skills_root"])
    target_names = {target["name"] for target in manifest["targets"]}
    allowed = {validate_allowed_path(value, target_names) for value in allow}
    changed: dict[str, list[str]] = {"added": [], "modified": [], "removed": []}
    kinds: dict[str, str] = {}
    missing_targets: list[str] = []

    for target in manifest["targets"]:
        current = scan_target_state(root, target)
        if current["state"] != "present":
            missing_targets.append(target["name"])
            continue
        difference = diff_entries(target["entries"], current["entries"])
        before = entry_map(target["entries"])
        after = entry_map(current["entries"])
        for category, paths in difference.items():
            for relative in paths:
                rooted = f"{target['name']}/{relative}"
                changed[category].append(rooted)
                entry = after.get(relative) or before.get(relative)
                if entry is not None:
                    kinds[rooted] = entry["kind"]

    for paths in changed.values():
        paths.sort()
    changed_paths = set().union(*changed.values())
    unexpected = sorted(
        path
        for path in changed_paths
        if not (
            path in allowed
            or (kinds.get(path) == "directory" and directory_change_allowed(path, allowed))
        )
    )
    report = {
        "allowed_unchanged": sorted(allowed - changed_paths),
        "changed": changed,
        "missing_targets": sorted(missing_targets),
        "status": "verified" if not unexpected and not missing_targets else "failed",
        "unexpected": unexpected,
    }
    return not unexpected and not missing_targets, report


def render_json(value: dict[str, Any]) -> None:
    """Render one deterministic JSON report to standard output."""

    json.dump(value, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def parse_args() -> argparse.Namespace:
    """Parse the scope-guard command line."""

    parser = argparse.ArgumentParser(
        description="Snapshot and verify approved user-level skill filesystem scope."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    snapshot = commands.add_parser("snapshot", help="record approved target baselines")
    snapshot.add_argument("--skills-root", type=Path, required=True)
    snapshot.add_argument("--existing", action="append", default=[])
    snapshot.add_argument("--new", action="append", default=[])
    snapshot.add_argument("--output", type=Path, required=True)

    unchanged = commands.add_parser(
        "unchanged", help="fail when a targeted baseline drifted"
    )
    unchanged.add_argument("--snapshot", type=Path, required=True)

    verify = commands.add_parser(
        "verify", help="fail when a targeted package changed outside the allowlist"
    )
    verify.add_argument("--snapshot", type=Path, required=True)
    verify.add_argument("--allow", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    """Run the requested scope-guard operation."""

    args = parse_args()
    try:
        if args.command == "snapshot":
            manifest = create_snapshot(
                args.skills_root, args.existing, args.new, args.output
            )
            render_json(manifest)
            return 0
        if args.command == "unchanged":
            unchanged, report = check_unchanged(args.snapshot)
            render_json(report)
            return 0 if unchanged else 1
        verified, report = verify_snapshot(args.snapshot, args.allow)
        render_json(report)
        return 0 if verified else 1
    except GuardError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
