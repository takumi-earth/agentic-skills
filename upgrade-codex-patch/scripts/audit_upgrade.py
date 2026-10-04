#!/usr/bin/env python3
"""Inspect a carried patch upgrade without modifying the audited repository."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from pathlib import PurePosixPath

from compare_patch_hunks import compare_patches
from compare_patch_hunks import parse_patch


class AuditError(ValueError):
    def __init__(self, condition: str, expected: object, received: object):
        super().__init__(condition)
        self.details = {
            "condition": condition,
            "expected": expected,
            "received": received,
        }


def display(path: Path) -> str:
    path = path.absolute()
    try:
        return "~/" + path.relative_to(Path.home()).as_posix()
    except ValueError:
        return str(path)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [
            "git",
            "--literal-pathspecs",
            "-c",
            "core.fsmonitor=false",
            "-C",
            str(repo),
            *args,
        ],
        capture_output=True,
        check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )
    if check and result.returncode:
        raise AuditError(
            "git command succeeds",
            {"argv": list(args), "exit_code": 0},
            {
                "exit_code": result.returncode,
                "stderr": result.stderr.decode(errors="replace"),
            },
        )
    return result


def git_paths(data: bytes) -> list[str]:
    return [os.fsdecode(path) for path in data.split(b"\0") if path]


def relative_paths(paths: list[str]) -> list[str]:
    for path in paths:
        parts = PurePosixPath(path)
        if (
            parts.is_absolute()
            or ".." in parts.parts
            or parts.as_posix() != path
            or path == "."
        ):
            raise AuditError(
                "paths are canonical repository-relative paths", "relative path", path
            )
    return sorted(set(paths))


def patch_metadata(path: Path) -> dict:
    data = path.read_bytes()
    files = parse_patch(path)
    return {
        "path": display(path),
        "sha256": digest(data),
        "bytes": len(data),
        "lines": len(data.splitlines()),
        "paths": relative_paths(list(files)),
        "hunks": sum(len(file.hunks) for file in files.values()),
    }


def snapshot(
    repo: Path, previous_patch: Path, excluded: list[str], included: list[str]
) -> dict:
    repo = Path(
        os.fsdecode(git(repo, "rev-parse", "--show-toplevel").stdout).strip()
    ).resolve()
    predecessor = patch_metadata(previous_patch)
    tracked = git_paths(git(repo, "ls-files", "-z").stdout)
    changed = git_paths(git(repo, "diff", "--name-only", "-z", "HEAD").stdout)
    untracked = git_paths(
        git(repo, "ls-files", "--others", "--exclude-standard", "-z").stdout
    )
    manifest_paths = {
        path for path in tracked if PurePosixPath(path).name == "Cargo.toml"
    }
    surface = relative_paths(
        list(set(changed) | set(predecessor["paths"]) | set(included) | set(excluded))
        + [
            path
            for path in tracked + untracked
            if PurePosixPath(path).name in {"Cargo.toml", "Cargo.lock"}
        ]
    )
    files = {}
    manifests = {}
    bytes_read = 0
    for name in surface:
        path = repo / name
        if path.is_symlink():
            data = os.fsencode(os.readlink(path))
            kind = "symlink"
        elif path.is_file():
            data = path.read_bytes()
            kind = "file"
        elif not path.exists():
            files[name] = None
            continue
        else:
            raise AuditError(
                "snapshot surface contains files", "file or absent path", name
            )
        files[name] = {"kind": kind, "sha256": digest(data), "bytes": len(data)}
        bytes_read += len(data)
        if name in manifest_paths and kind == "file":
            manifests[name] = tomllib.loads(data.decode("utf-8"))

    exact_pins = []
    for name, manifest in manifests.items():
        tables = [
            (key, manifest[key])
            for key in ("dependencies", "dev-dependencies", "build-dependencies")
            if key in manifest
        ]
        if "dependencies" in manifest.get("workspace", {}):
            tables.append(
                ("workspace.dependencies", manifest["workspace"]["dependencies"])
            )
        for target, config in manifest.get("target", {}).items():
            tables.extend(
                (f"target.{target}.{key}", config[key])
                for key in ("dependencies", "dev-dependencies", "build-dependencies")
                if key in config
            )
        workspace_name = None
        current = PurePosixPath(name).parent
        explicit_workspace = manifest.get("package", {}).get("workspace")
        if explicit_workspace is not None:
            workspace_name = (
                (repo / current / explicit_workspace / "Cargo.toml")
                .resolve()
                .relative_to(repo)
                .as_posix()
            )
        else:
            for directory in (current, *current.parents):
                candidate = (directory / "Cargo.toml").as_posix()
                if "workspace" in manifests.get(candidate, {}):
                    workspace_name = candidate
                    break
        for table_name, dependencies in tables:
            for dependency, requirement in dependencies.items():
                owner = name
                if isinstance(requirement, dict) and requirement.get("workspace"):
                    owner = workspace_name
                    requirement = (
                        manifests.get(owner, {})
                        .get("workspace", {})
                        .get("dependencies", {})
                        .get(dependency)
                    )
                    if requirement is None:
                        raise AuditError(
                            "inherited dependency has a workspace owner",
                            dependency,
                            {"manifest": name, "workspace": owner},
                        )
                if not isinstance(requirement, (str, dict)):
                    raise AuditError(
                        "dependency requirement has a supported shape",
                        "string or table",
                        {
                            "manifest": name,
                            "dependency": dependency,
                            "requirement": requirement,
                        },
                    )
                version = (
                    requirement
                    if isinstance(requirement, str)
                    else requirement.get("version")
                )
                if isinstance(version, str) and version.startswith("="):
                    exact_pins.append(
                        {
                            "manifest": name,
                            "table": table_name,
                            "dependency": dependency,
                            "requirement": version,
                            "source_manifest": owner,
                        }
                    )

    index = git(repo, "ls-files", "--stage", "-z").stdout
    tag = git(repo, "describe", "--tags", "--exact-match", "HEAD", check=False)
    predecessor_export = (
        git(
            repo,
            "diff",
            "--binary",
            "--no-ext-diff",
            "--no-textconv",
            "HEAD",
            "--",
            *predecessor["paths"],
        ).stdout
        if predecessor["paths"]
        else b""
    )
    predecessor_index_export = (
        git(
            repo,
            "diff",
            "--cached",
            "--binary",
            "--no-ext-diff",
            "--no-textconv",
            "HEAD",
            "--",
            *predecessor["paths"],
        ).stdout
        if predecessor["paths"]
        else b""
    )
    index_path = Path(
        os.fsdecode(git(repo, "rev-parse", "--git-path", "index").stdout).strip()
    )
    if not index_path.is_absolute():
        index_path = repo / index_path
    return {
        "schema_version": 1,
        "kind": "snapshot",
        "repo": display(repo),
        "head": git(repo, "rev-parse", "HEAD").stdout.decode().strip(),
        "tag": tag.stdout.decode().strip() if tag.returncode == 0 else None,
        "previous_patch": predecessor,
        "predecessor_worktree_export_sha256": digest(predecessor_export),
        "predecessor_index_export_sha256": digest(predecessor_index_export),
        "excluded_paths": relative_paths(excluded),
        "included_paths": relative_paths(included),
        "index_sha256": digest(index),
        "index_bytes_sha256": digest(index_path.read_bytes()),
        "index_pristine": not git(
            repo, "diff", "--cached", "--name-only", "-z", "HEAD"
        ).stdout,
        "changed_paths": sorted(changed),
        "untracked_paths": sorted(untracked),
        "files": files,
        "exact_pins": exact_pins,
        "observation": {
            "tracked_paths": len(tracked),
            "surface_paths": len(surface),
            "files_read": sum(value is not None for value in files.values()),
            "bytes_read": bytes_read,
        },
    }


def read_snapshot(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    fields = {
        "repo": str,
        "head": str,
        "previous_patch": dict,
        "excluded_paths": list,
        "included_paths": list,
        "index_sha256": str,
        "index_pristine": bool,
        "changed_paths": list,
        "untracked_paths": list,
        "files": dict,
        "exact_pins": list,
    }
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != 1
        or value.get("kind") != "snapshot"
        or any(not isinstance(value.get(key), kind) for key, kind in fields.items())
    ):
        raise AuditError(
            "snapshot schema is supported and complete",
            "version 1 snapshot",
            display(path),
        )
    predecessor = value["previous_patch"]
    if (
        not isinstance(predecessor.get("path"), str)
        or not isinstance(predecessor.get("paths"), list)
        or not isinstance(predecessor.get("sha256"), str)
    ):
        raise AuditError(
            "snapshot predecessor is complete", "patch metadata", predecessor
        )
    for field in (
        "predecessor_worktree_export_sha256",
        "predecessor_index_export_sha256",
        "index_bytes_sha256",
    ):
        export_digest = value.get(field)
        if export_digest is not None and (
            not isinstance(export_digest, str)
            or len(export_digest) != 64
            or any(character not in "0123456789abcdef" for character in export_digest)
        ):
            raise AuditError(
                "snapshot export/index digest is valid",
                {
                    "field": field,
                    "value": "SHA-256 or an older snapshot without this field",
                },
                export_digest,
            )
    for key in ("excluded_paths", "included_paths", "changed_paths", "untracked_paths"):
        if not all(isinstance(name, str) for name in value[key]):
            raise AuditError("snapshot paths are strings", key, value[key])
        relative_paths(value[key])
    return value


def changes(before: dict, after: dict) -> dict:
    for field in ("repo", "excluded_paths", "included_paths"):
        if before[field] != after[field]:
            raise AuditError(
                "snapshot scopes match", {field: before[field]}, {field: after[field]}
            )
    names = sorted(before["files"].keys() | after["files"].keys())
    changed = [
        name for name in names if before["files"].get(name) != after["files"].get(name)
    ]
    checks = [
        {
            "condition": condition,
            "expected": before[field],
            "received": after[field],
            "status": "passed" if before[field] == after[field] else "failed",
        }
        for condition, field in (
            ("HEAD is unchanged", "head"),
            ("index entries are unchanged", "index_sha256"),
            ("previous patch is unchanged", "previous_patch"),
        )
    ]
    if "index_bytes_sha256" in before:
        checks.append(
            {
                "condition": "index bytes are unchanged",
                "expected": before["index_bytes_sha256"],
                "received": after.get("index_bytes_sha256"),
                "status": "passed"
                if before["index_bytes_sha256"] == after.get("index_bytes_sha256")
                else "failed",
            }
        )
    return {
        "schema_version": 1,
        "kind": "changes",
        "status": "passed"
        if all(check["status"] == "passed" for check in checks)
        else "failed",
        "repo": before["repo"],
        "changed_paths": changed,
        "dependency_files": [
            name
            for name in changed
            if PurePosixPath(name).name in {"Cargo.toml", "Cargo.lock"}
        ],
        "other_paths": [
            name
            for name in changed
            if PurePosixPath(name).name not in {"Cargo.toml", "Cargo.lock"}
        ],
        "head_unchanged": before["head"] == after["head"],
        "index_unchanged": before["index_sha256"] == after["index_sha256"],
        "previous_patch_unchanged": before["previous_patch"] == after["previous_patch"],
        "new_untracked_paths": sorted(
            set(after["untracked_paths"]) - set(before["untracked_paths"])
        ),
        "checks": checks,
    }


def check_target_base(
    repo: Path, head: str, successor: Path, paths: list[str], scratch_root: Path
):
    scratch_root = scratch_root.expanduser().resolve()
    if scratch_root.is_relative_to(repo.resolve()) or not scratch_root.is_dir():
        raise AuditError(
            "applicability scratch is an existing external directory",
            "external scratch directory",
            display(scratch_root),
        )
    git_dir = os.fsdecode(git(repo, "rev-parse", "--absolute-git-dir").stdout).strip()
    with tempfile.TemporaryDirectory(
        dir=scratch_root, prefix="target-base-"
    ) as temporary:
        tree = Path(temporary)
        for name in paths:
            entry = git(repo, "ls-tree", "-z", head, "--", name).stdout
            if not entry:
                continue
            descriptor, actual_name = entry.rstrip(b"\0").split(b"\t", 1)
            mode, kind, object_id = descriptor.split()
            if kind != b"blob" or os.fsdecode(actual_name) != name:
                raise AuditError(
                    "patch base entries are exact blobs", name, os.fsdecode(entry)
                )
            destination = tree / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            data = git(repo, "cat-file", "blob", object_id.decode("ascii")).stdout
            if mode == b"120000":
                destination.symlink_to(os.fsdecode(data))
            elif mode in {b"100644", b"100755"}:
                destination.write_bytes(data)
                destination.chmod(int(mode, 8) & 0o777)
            else:
                raise AuditError(
                    "patch base blob mode is supported",
                    "regular file or symlink",
                    mode.decode(),
                )
        return git(
            tree,
            f"--git-dir={git_dir}",
            f"--work-tree={tree}",
            "apply",
            "--check",
            str(successor),
            check=False,
        )


def audit(
    baseline: dict,
    successor: Path,
    included: list[str],
    selected_export: Path,
    scratch_root: Path,
) -> dict:
    repo = Path(baseline["repo"]).expanduser()
    predecessor = Path(baseline["previous_patch"]["path"]).expanduser()
    current = snapshot(
        repo,
        predecessor,
        baseline["excluded_paths"],
        sorted(set(baseline["included_paths"]) | set(included)),
    )
    metadata = patch_metadata(successor)
    selection = patch_metadata(selected_export)
    if (
        selected_export.resolve() == successor.resolve()
        or selected_export.resolve().is_relative_to(repo.resolve())
    ):
        raise AuditError(
            "reviewed selection is a separate external input",
            "frozen reviewed export outside the audited repository",
            display(selected_export),
        )
    comparison = compare_patches(parse_patch(predecessor), parse_patch(successor))
    intended = sorted(
        (set(baseline["previous_patch"]["paths"]) | set(current["included_paths"]))
        - set(baseline["excluded_paths"])
    )
    checks = []

    def require(condition: str, expected: object, received: object):
        checks.append(
            {
                "condition": condition,
                "expected": expected,
                "received": received,
                "status": "passed" if expected == received else "failed",
            }
        )

    require("HEAD is unchanged", baseline["head"], current["head"])
    require(
        "index entries are unchanged", baseline["index_sha256"], current["index_sha256"]
    )
    if "index_bytes_sha256" in baseline:
        require(
            "index bytes are unchanged",
            baseline["index_bytes_sha256"],
            current["index_bytes_sha256"],
        )
    require(
        "previous patch is unchanged",
        baseline["previous_patch"],
        current["previous_patch"],
    )
    require(
        "successor has a separate path",
        True,
        successor.resolve() != predecessor.resolve(),
    )
    require(
        "patch paths belong to the intended set",
        [],
        sorted(set(metadata["paths"]) - set(intended)),
    )
    recorded_predecessor_paths = (
        set(baseline["previous_patch"]["paths"])
        if baseline["previous_patch"]["sha256"]
        in {
            baseline.get("predecessor_worktree_export_sha256"),
            baseline.get("predecessor_index_export_sha256"),
        }
        else set()
    )
    require(
        "pre-existing export edits have recorded predecessor provenance",
        [],
        sorted(
            (set(baseline["changed_paths"]) & set(metadata["paths"]))
            - recorded_predecessor_paths
        ),
    )
    require(
        "authorized untracked additions are included in the selected export",
        [],
        sorted(
            (set(current["untracked_paths"]) & set(intended)) - set(metadata["paths"])
        ),
    )
    allowed = (
        set(intended) | set(baseline["excluded_paths"]) | set(baseline["changed_paths"])
    )
    require(
        "new changed paths are accounted for",
        [],
        sorted(set(current["changed_paths"]) - allowed),
    )
    require(
        "new untracked paths are accounted for",
        [],
        sorted(
            set(current["untracked_paths"])
            - set(baseline["untracked_paths"])
            - set(baseline["excluded_paths"])
            - set(current["included_paths"])
        ),
    )
    preserved = (
        set(baseline["changed_paths"]) - set(intended) - set(baseline["excluded_paths"])
    )
    require(
        "unrelated pre-existing edits are preserved",
        [],
        sorted(
            name
            for name in preserved
            if baseline["files"].get(name) != current["files"].get(name)
        ),
    )
    require(
        "successor bytes equal the reviewed hunk selection",
        selection["sha256"],
        metadata["sha256"],
    )
    applicability = {}
    for label, args in (("cached", ["--cached"]), ("target_base", [])):
        if label == "cached" and not current["index_pristine"]:
            applicability[label] = {
                "status": "not-run",
                "reason": "index is not pristine; preserve it and use the private target-base filesystem check",
            }
            continue
        result = (
            git(repo, "apply", "--check", *args, str(successor), check=False)
            if label == "cached"
            else check_target_base(
                repo, baseline["head"], successor, metadata["paths"], scratch_root
            )
        )
        applicability[label] = {
            "status": "passed" if result.returncode == 0 else "failed",
            "exit_code": result.returncode,
            "stdout": result.stdout.decode(errors="replace"),
            "stderr": result.stderr.decode(errors="replace"),
        }
        require(f"{label} applicability succeeds", 0, result.returncode)
    return {
        "schema_version": 1,
        "kind": "audit",
        "status": "passed"
        if all(check["status"] == "passed" for check in checks)
        else "failed",
        "repo": current["repo"],
        "head": current["head"],
        "tag": current["tag"],
        "successor": metadata,
        "reviewed_selection": selection,
        "intended_paths": intended,
        "excluded_paths": baseline["excluded_paths"],
        "checks": checks,
        "applicability": applicability,
        "comparison": {
            "common_files": len(comparison.common),
            "identical_edit_streams": sum(
                item.identical_edits for item in comparison.common
            ),
            "differing_paths": [item.path for item in comparison.differing],
            "old_only_paths": list(comparison.old_only),
            "new_only_paths": list(comparison.new_only),
            "identical_hunk_edit_streams": sum(
                item.exact_hunks for item in comparison.common
            ),
        },
        "exact_pins": current["exact_pins"],
    }


def normalize_home(value):
    if isinstance(value, str):
        return value.replace(str(Path.home()) + os.sep, "~/").replace(
            Path.home().as_posix() + "/", "~/"
        )
    if isinstance(value, dict):
        return {
            normalize_home(key): normalize_home(item) for key, item in value.items()
        }
    if isinstance(value, list):
        return [normalize_home(item) for item in value]
    return value


def emit(report: dict, output: Path | None):
    rendered = json.dumps(normalize_home(report), indent=2, sort_keys=True) + "\n"
    if output is not None:
        output = output.expanduser().resolve()
        repo = report.get("repo")
        if repo is not None and output.is_relative_to(
            Path(repo).expanduser().resolve()
        ):
            raise AuditError(
                "evidence is outside the audited repository",
                "external report path",
                display(output),
            )
        output.parent.mkdir(parents=True, exist_ok=True)
        staging = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=output.parent, delete=False
            ) as stream:
                staging = Path(stream.name)
                stream.write(rendered)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(staging, output)
        finally:
            if staging is not None:
                staging.unlink()
    sys.stdout.write(rendered)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    capture = subparsers.add_parser(
        "snapshot", help="record patch provenance and the expected mutation surface"
    )
    capture.add_argument("--repo", type=Path, required=True)
    capture.add_argument("--previous-patch", type=Path, required=True)
    capture.add_argument("--exclude", action="append", default=[])
    capture.add_argument("--include", action="append", default=[])
    delta = subparsers.add_parser(
        "changes", help="compare two snapshots after a Cargo command"
    )
    delta.add_argument("--before", type=Path, required=True)
    delta.add_argument("--after", type=Path, required=True)
    finish = subparsers.add_parser(
        "audit", help="check the final artifact against the pre-application baseline"
    )
    finish.add_argument("--baseline", type=Path, required=True)
    finish.add_argument("--successor-patch", type=Path, required=True)
    finish.add_argument("--include", action="append", default=[])
    finish.add_argument(
        "--selected-export",
        type=Path,
        required=True,
        help="frozen reviewed hunk selection; never a whole-worktree path export",
    )
    finish.add_argument(
        "--scratch-root",
        type=Path,
        required=True,
        help="existing external directory for a disposable target-base applicability view",
    )
    for command in (capture, delta, finish):
        command.add_argument(
            "--output",
            type=Path,
            help="exclusively publish JSON outside the audited repository",
        )
    args = parser.parse_args(argv)
    try:
        if args.operation == "snapshot":
            report = snapshot(
                args.repo.expanduser(),
                args.previous_patch.expanduser().absolute(),
                relative_paths(args.exclude),
                relative_paths(args.include),
            )
        elif args.operation == "changes":
            report = changes(
                read_snapshot(args.before.expanduser()),
                read_snapshot(args.after.expanduser()),
            )
        else:
            report = audit(
                read_snapshot(args.baseline.expanduser()),
                args.successor_patch.expanduser().absolute(),
                relative_paths(args.include),
                args.selected_export.expanduser().absolute(),
                args.scratch_root,
            )
        emit(report, args.output)
        return 1 if report.get("status") == "failed" else 0
    except (AuditError, OSError, ValueError) as error:
        details = (
            error.details
            if isinstance(error, AuditError)
            else {
                "condition": "inspection and report publication succeed",
                "expected": "readable inputs and an unused output path",
                "received": str(error),
            }
        )
        emit(
            {
                "schema_version": 1,
                "kind": "error",
                "status": "failed",
                "error": details,
            },
            None,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
