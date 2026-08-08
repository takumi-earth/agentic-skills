#!/usr/bin/env python3
"""Resolve the canonical Agentic Skills checkout by remote identity."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Iterable
from urllib.parse import urlsplit


CANONICAL_REMOTE = "https://github.com/takumi-earth/agentic-skills.git"
CANONICAL_IDENTITY = "github.com/takumi-earth/agentic-skills"
DEFAULT_MAX_DEPTH = 6
PRUNED_DIRECTORY_NAMES = {
    ".cache",
    ".git",
    ".npm",
    ".rustup",
    ".cargo",
    ".scratchpad",
    "node_modules",
    "target",
}


class ResolutionError(RuntimeError):
    """No canonical checkout could be resolved safely."""


def normalize_remote(value: str) -> str | None:
    """Normalize common HTTPS, SSH, and scp-style GitHub remote spellings."""
    raw = value.strip()
    if not raw:
        return None
    if "://" in raw:
        parsed = urlsplit(raw)
        host = (parsed.hostname or "").casefold()
        path = parsed.path
    else:
        match = re.fullmatch(r"(?:[^@/]+@)?([^:/]+):(.+)", raw)
        if match is None:
            return None
        host, path = match.groups()
        host = host.casefold()
    if host == "www.github.com":
        host = "github.com"
    normalized_path = path.strip("/")
    if normalized_path.casefold().endswith(".git"):
        normalized_path = normalized_path[:-4]
    if not host or not normalized_path:
        return None
    return f"{host}/{normalized_path}".casefold()


def run_git(arguments: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run one read-only Git query with deterministic output settings."""
    environment = os.environ.copy()
    environment["GIT_TERMINAL_PROMPT"] = "0"
    environment["LC_ALL"] = "C"
    return subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )


def git_root(candidate: Path) -> Path | None:
    """Resolve a worktree candidate to its top-level Git directory."""
    if not candidate.exists() or not candidate.is_dir():
        return None
    completed = run_git(["rev-parse", "--show-toplevel"], cwd=candidate)
    if completed.returncode != 0:
        return None
    return Path(completed.stdout.strip()).resolve()


def remote_urls(root: Path) -> list[str]:
    """Return every local remote URL and push URL configured for one checkout."""
    completed = run_git(
        ["config", "--local", "--get-regexp", r"^remote\..*\.(url|pushurl)$"],
        cwd=root,
    )
    if completed.returncode not in {0, 1}:
        raise ResolutionError(
            f"cannot read remotes for {root}: exit={completed.returncode}; "
            f"stderr={completed.stderr.strip()!r}"
        )
    output: list[str] = []
    for line in completed.stdout.splitlines():
        _, separator, value = line.partition(" ")
        if separator and value:
            output.append(value.strip())
    return sorted(set(output))


def path_distance(home: Path, candidate: Path) -> int:
    """Return component distance between the home directory and a checkout."""
    resolved_home = home.resolve()
    resolved_candidate = candidate.resolve()
    try:
        common = Path(os.path.commonpath([resolved_home, resolved_candidate]))
    except ValueError:
        return 1_000_000 + len(resolved_candidate.parts)
    return len(resolved_home.relative_to(common).parts) + len(
        resolved_candidate.relative_to(common).parts
    )


def render_path(path: Path, home: Path) -> str:
    """Render paths beneath home with a portable tilde prefix."""

    resolved_path = path.expanduser().resolve(strict=False)
    resolved_home = home.expanduser().resolve(strict=False)
    try:
        relative = resolved_path.relative_to(resolved_home)
    except ValueError:
        return str(resolved_path)
    if relative == Path("."):
        return "~"
    return f"~/{relative.as_posix()}"


def ancestor_candidates(path: Path) -> Iterable[Path]:
    """Yield a path and each directory ancestor once."""
    resolved = path.resolve()
    if resolved.is_file():
        resolved = resolved.parent
    yield resolved
    yield from resolved.parents


def discover_git_directories(root: Path, max_depth: int) -> Iterable[Path]:
    """Find bounded worktree candidates without following directory symlinks."""
    source = root.expanduser().resolve()
    if not source.is_dir():
        return
    for directory, names, filenames in os.walk(source, followlinks=False):
        path = Path(directory)
        depth = len(path.relative_to(source).parts)
        has_git_directory = ".git" in names
        names[:] = sorted(
            name
            for name in names
            if name not in PRUNED_DIRECTORY_NAMES
            and not (path / name).is_symlink()
        )
        if ".git" in filenames or has_git_directory:
            yield path
        if depth >= max_depth:
            names[:] = []


def resolve_repository(
    *,
    home: Path,
    explicit_candidates: Iterable[Path],
    search_roots: Iterable[Path],
    max_depth: int,
    executing_path: Path | None,
) -> dict[str, object]:
    """Resolve, validate, rank, and report canonical checkout candidates."""
    raw_candidates: list[tuple[str, Path]] = []
    raw_candidates.extend(("explicit", candidate) for candidate in explicit_candidates)
    environment_candidate = os.environ.get("AGENTIC_SKILLS_REPO")
    if environment_candidate:
        raw_candidates.append(("environment", Path(environment_candidate)))
    if executing_path is not None:
        raw_candidates.extend(
            ("executing-package", candidate)
            for candidate in ancestor_candidates(executing_path)
        )
    raw_candidates.extend(("cwd", candidate) for candidate in ancestor_candidates(Path.cwd()))
    for search_root in search_roots:
        raw_candidates.extend(
            ("bounded-search", candidate)
            for candidate in discover_git_directories(search_root, max_depth)
        )

    executing_root = None
    if executing_path is not None:
        resolved_executing_path = executing_path.resolve()
        executing_root = git_root(
            resolved_executing_path.parent
            if resolved_executing_path.is_file()
            else resolved_executing_path
        )
    roots: dict[Path, set[str]] = {}
    for source, candidate in raw_candidates:
        root = git_root(candidate)
        if root is not None:
            roots.setdefault(root, set()).add(source)

    valid: list[tuple[dict[str, object], Path]] = []
    rejected: list[dict[str, object]] = []
    for root in sorted(roots):
        urls = remote_urls(root)
        normalized = sorted(
            {identity for url in urls if (identity := normalize_remote(url)) is not None}
        )
        package_present = (root / "auto-skill-creator" / "SKILL.md").is_file()
        record: dict[str, object] = {
            "path": render_path(root, home),
            "sources": sorted(roots[root]),
            "remote_urls": urls,
            "normalized_remote_identities": normalized,
            "distance_from_home": path_distance(home, root),
            "contains_executing_package": executing_root == root,
            "contains_auto_skill_creator": package_present,
        }
        if CANONICAL_IDENTITY in normalized and package_present:
            valid.append((record, root))
        else:
            record["rejection"] = (
                "remote_identity_mismatch"
                if CANONICAL_IDENTITY not in normalized
                else "auto_skill_creator_package_missing"
            )
            rejected.append(record)

    if not valid:
        raise ResolutionError(
            "no checkout matched canonical remote identity "
            f"{CANONICAL_IDENTITY!r}; examined_roots={len(roots)}"
        )
    valid.sort(
        key=lambda item: (
            int(item[0]["distance_from_home"]),
            0 if item[0]["contains_executing_package"] else 1,
            str(item[0]["path"]),
        )
    )
    selected, selected_root = valid[0]
    return {
        "schema_version": 1,
        "canonical_remote": CANONICAL_REMOTE,
        "canonical_identity": CANONICAL_IDENTITY,
        "home": render_path(home, home),
        "selection_policy": (
            "minimum filesystem component distance from home; executing-package "
            "checkout then lexical path break equal-distance ties"
        ),
        "selected": selected,
        "scratchpad_root": render_path(selected_root / ".scratchpad", home),
        "valid_candidates": [record for record, _ in valid],
        "rejected_candidates": rejected,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, action="append", default=[])
    parser.add_argument("--search-root", type=Path, action="append")
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    search_roots = arguments.search_root or [arguments.home]
    try:
        report = resolve_repository(
            home=arguments.home,
            explicit_candidates=arguments.candidate,
            search_roots=search_roots,
            max_depth=arguments.max_depth,
            executing_path=Path(__file__).resolve(),
        )
    except ResolutionError as error:
        print(f"RESOLUTION_ERROR: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
