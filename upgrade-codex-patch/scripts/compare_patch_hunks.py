#!/usr/bin/env python3
"""Compare the normalized edit streams of two Git-style unified patches."""

import argparse
import shlex
import sys
from dataclasses import dataclass, field
from difflib import SequenceMatcher, unified_diff
from pathlib import Path


class PatchParseError(ValueError):
    """Report an input that is not a supported Git-style unified patch."""


@dataclass
class Hunk:
    header: str
    edits: list[str] = field(default_factory=list)


@dataclass
class PatchedFile:
    path: str
    hunks: list[Hunk] = field(default_factory=list)

    @property
    def edit_stream(self) -> tuple[str, ...]:
        return tuple(edit for hunk in self.hunks for edit in hunk.edits)

    @property
    def hunk_fingerprints(self) -> tuple[tuple[str, ...], ...]:
        return tuple(tuple(hunk.edits) for hunk in self.hunks)


@dataclass(frozen=True)
class FileComparison:
    path: str
    old: PatchedFile
    new: PatchedFile
    exact_hunks: int

    @property
    def identical_edits(self) -> bool:
        return self.old.edit_stream == self.new.edit_stream


@dataclass(frozen=True)
class PatchComparison:
    old_only: tuple[str, ...]
    new_only: tuple[str, ...]
    common: tuple[FileComparison, ...]

    @property
    def differing(self) -> tuple[FileComparison, ...]:
        return tuple(item for item in self.common if not item.identical_edits)

    @property
    def is_identical(self) -> bool:
        return not self.old_only and not self.new_only and not self.differing


def _git_target_path(header: str, line_number: int) -> str:
    try:
        fields = shlex.split(header)
    except ValueError as exc:
        raise PatchParseError(f"line {line_number}: malformed diff header: {exc}") from exc
    if len(fields) != 4 or fields[:2] != ["diff", "--git"]:
        raise PatchParseError(f"line {line_number}: unsupported diff header: {header}")
    target = fields[3]
    return target[2:] if target.startswith("b/") else target


def parse_patch(path: Path) -> dict[str, PatchedFile]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise PatchParseError(f"cannot read {path}: {exc}") from exc

    files: dict[str, PatchedFile] = {}
    current_file: PatchedFile | None = None
    current_hunk: Hunk | None = None

    for line_number, line in enumerate(lines, start=1):
        if line.startswith("diff --git "):
            target = _git_target_path(line, line_number)
            if target in files:
                raise PatchParseError(
                    f"line {line_number}: repeated diff section for {target}"
                )
            current_file = PatchedFile(path=target)
            files[target] = current_file
            current_hunk = None
            continue

        if line.startswith("@@ "):
            if current_file is None:
                raise PatchParseError(
                    f"line {line_number}: hunk appears before a Git diff header"
                )
            current_hunk = Hunk(header=line)
            current_file.hunks.append(current_hunk)
            continue

        if current_hunk is not None and line.startswith(("+", "-")):
            current_hunk.edits.append(line)

    if not files:
        raise PatchParseError(f"{path} contains no `diff --git` sections")

    without_hunks = [patched_file.path for patched_file in files.values() if not patched_file.hunks]
    if without_hunks:
        joined = ", ".join(without_hunks)
        raise PatchParseError(
            "unsupported non-text or metadata-only diff sections: " + joined
        )

    return files


def _exact_hunk_count(old: PatchedFile, new: PatchedFile) -> int:
    matcher = SequenceMatcher(
        None,
        old.hunk_fingerprints,
        new.hunk_fingerprints,
        autojunk=False,
    )
    return sum(block.size for block in matcher.get_matching_blocks())


def compare_patches(
    old_files: dict[str, PatchedFile], new_files: dict[str, PatchedFile]
) -> PatchComparison:
    old_paths = set(old_files)
    new_paths = set(new_files)
    common = tuple(
        FileComparison(
            path=path,
            old=old_files[path],
            new=new_files[path],
            exact_hunks=_exact_hunk_count(old_files[path], new_files[path]),
        )
        for path in sorted(old_paths & new_paths)
    )
    return PatchComparison(
        old_only=tuple(sorted(old_paths - new_paths)),
        new_only=tuple(sorted(new_paths - old_paths)),
        common=common,
    )


def _print_paths(label: str, paths: tuple[str, ...]) -> None:
    print(f"{label}={len(paths)}")
    for path in paths:
        print(f"  {path}")


def render_comparison(
    comparison: PatchComparison,
    old_path: Path,
    new_path: Path,
    *,
    summary_only: bool,
) -> None:
    identical = tuple(item for item in comparison.common if item.identical_edits)
    print("PATCH HUNK COMPARISON")
    print(f"old={old_path}")
    print(f"new={new_path}")
    print(f"common_files={len(comparison.common)}")
    print(f"identical_edit_streams={len(identical)}")
    print(f"differing_edit_streams={len(comparison.differing)}")
    _print_paths("old_only_files", comparison.old_only)
    _print_paths("new_only_files", comparison.new_only)
    print("common_file_results:")
    for item in comparison.common:
        state = "IDENTICAL" if item.identical_edits else "DIFFERS"
        print(
            f"  {state} {item.path} "
            f"exact_hunks={item.exact_hunks} "
            f"old_hunks={len(item.old.hunks)} "
            f"new_hunks={len(item.new.hunks)} "
            f"old_edits={len(item.old.edit_stream)} "
            f"new_edits={len(item.new.edit_stream)}"
        )
        if item.identical_edits or summary_only:
            continue
        diff = unified_diff(
            item.old.edit_stream,
            item.new.edit_stream,
            fromfile=f"old:{item.path}:normalized-edits",
            tofile=f"new:{item.path}:normalized-edits",
            lineterm="",
            n=4,
        )
        for line in diff:
            print(f"    {line}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare added and removed lines in Git-style unified patches while "
            "ignoring hunk offsets, index hashes, and unchanged context."
        )
    )
    parser.add_argument(
        "--require-identical",
        action="store_true",
        help="exit 1 when path sets or normalized edit streams differ",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="omit normalized unified diffs for changed common files",
    )
    parser.add_argument("old_patch", type=Path)
    parser.add_argument("new_patch", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        old_files = parse_patch(args.old_patch)
        new_files = parse_patch(args.new_patch)
    except PatchParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    comparison = compare_patches(old_files, new_files)
    render_comparison(
        comparison,
        args.old_patch,
        args.new_patch,
        summary_only=args.summary,
    )
    if args.require_identical and not comparison.is_identical:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
