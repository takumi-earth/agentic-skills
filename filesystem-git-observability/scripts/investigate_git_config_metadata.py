#!/usr/bin/env python3
"""Investigate Git-config lock-and-rename metadata behavior without gating on it.

The repository inventory and selected production repository are read-only.
Mutation experiments run only in a disposable `.scratchpad/` fixture and are
reported as observations, never as an implicit preservation requirement.
"""

from __future__ import annotations

import argparse
from collections import Counter
import grp
import hashlib
import json
import os
from pathlib import Path
import pwd
import stat
import subprocess
import sys
import tempfile
from typing import Any, Iterable


class InvestigationError(RuntimeError):
    pass


def clean_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for key in list(environment):
        if key in {
            "GIT_DIR",
            "GIT_WORK_TREE",
            "GIT_COMMON_DIR",
            "GIT_INDEX_FILE",
        } or key.startswith("GIT_CONFIG_KEY_") or key.startswith("GIT_CONFIG_VALUE_"):
            environment.pop(key, None)
    environment.pop("GIT_CONFIG_COUNT", None)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    environment["GIT_TERMINAL_PROMPT"] = "0"
    environment["LC_ALL"] = "C"
    return environment


ENVIRONMENT = clean_environment()


def run(
    arguments: list[str],
    *,
    cwd: Path | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        arguments,
        cwd=str(cwd) if cwd is not None else None,
        env=ENVIRONMENT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
    )
    if check and completed.returncode != 0:
        raise InvestigationError(
            "command exit check failed; condition=command exit code equals zero; "
            f"expected=0; received={completed.returncode}; command={arguments!r}; "
            f"stderr={completed.stderr.decode('utf-8', 'replace').strip()!r}"
        )
    return completed


def user_name(uid: int) -> str | None:
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return None


def group_name(gid: int) -> str | None:
    try:
        return grp.getgrgid(gid).gr_name
    except KeyError:
        return None


def metadata(path: Path) -> dict[str, Any]:
    value = path.lstat()
    return {
        "path": str(path),
        "file_type": (
            "regular"
            if stat.S_ISREG(value.st_mode)
            else "directory"
            if stat.S_ISDIR(value.st_mode)
            else "symlink"
            if stat.S_ISLNK(value.st_mode)
            else "other"
        ),
        "mode_octal": f"0o{stat.S_IMODE(value.st_mode):04o}",
        "mode_symbolic": stat.filemode(value.st_mode),
        "uid": value.st_uid,
        "user": user_name(value.st_uid),
        "gid": value.st_gid,
        "group": group_name(value.st_gid),
        "inode": value.st_ino,
        "device": value.st_dev,
        "link_count": value.st_nlink,
        "size": value.st_size,
        "mtime_ns": value.st_mtime_ns,
        "ctime_ns": value.st_ctime_ns,
    }


def tuple_from_metadata(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": value["mode_octal"],
        "uid": value["uid"],
        "user": value["user"],
        "gid": value["gid"],
        "group": value["group"],
    }


def load_inventory(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise InvestigationError(f"cannot load inventory {path}: {error}") from error
    if not isinstance(document, dict) or not isinstance(document.get("repositories"), list):
        received = type(document.get("repositories")).__name__ if isinstance(document, dict) else type(document).__name__
        raise InvestigationError(
            "inventory schema check failed; condition=root object contains a repositories list; "
            f"expected=list; received={received}"
        )
    return document


def find_repository(document: dict[str, Any], repository_id: str) -> dict[str, Any]:
    matches = [
        repository
        for repository in document["repositories"]
        if repository.get("id") == repository_id
    ]
    if len(matches) != 1:
        raise InvestigationError(
            "inventory repository cardinality check failed; "
            f"condition=repository id {repository_id!r} resolves exactly once; "
            f"expected=1; received={len(matches)}"
        )
    return matches[0]


def parse_failure_message(repository: dict[str, Any]) -> dict[str, Any] | None:
    removal = repository.get("removal")
    if not isinstance(removal, dict):
        return None
    message = removal.get("message")
    if not isinstance(message, str):
        return {"status": removal.get("status"), "message": message, "parsed": False}
    try:
        structured = json.loads(message)
    except json.JSONDecodeError:
        structured = message
    return {
        "status": removal.get("status"),
        "message": structured,
        "parsed": isinstance(structured, dict),
    }


def parse_null_config(data: bytes) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for record in data.split(b"\0"):
        if not record:
            continue
        if b"\n" not in record:
            raise InvestigationError(
                "Git config record shape check failed; "
                "condition=NUL record contains key/value newline; "
                f"expected=newline separator; received={record[:80]!r}"
            )
        key, value = record.split(b"\n", 1)
        entries.append(
            (
                key.decode("utf-8", "surrogateescape"),
                value.decode("utf-8", "surrogateescape"),
            )
        )
    return entries


def remote_section(key: str) -> str | None:
    if not key.casefold().startswith("remote."):
        return None
    if "." not in key[len("remote.") :]:
        return None
    return key.rsplit(".", 1)[0]


def target_remote_sections(
    entries: Iterable[tuple[str, str]], target_marker: str
) -> list[str]:
    grouped: dict[str, list[tuple[str, str]]] = {}
    for key, value in entries:
        section = remote_section(key)
        if section is not None:
            grouped.setdefault(section, []).append((key, value))
    target_folded = target_marker.casefold()
    return sorted(
        section
        for section, values in grouped.items()
        if any(
            target_folded in material.casefold()
            for material in (
                section,
                *(key for key, _ in values),
                *(value for _, value in values),
            )
        )
    )


def current_config_semantics(
    repository: dict[str, Any], target_marker: str
) -> dict[str, Any]:
    arguments = ["git", f"--git-dir={repository['common_git_dir']}"]
    if repository.get("local_config_access") == "explicit_work_tree_required":
        arguments.append(f"--work-tree={repository['path']}")
    arguments += ["config", "--local", "--no-includes", "--null", "--list"]
    completed = run(arguments)
    if completed.returncode != 0:
        return {
            "read_succeeded": False,
            "exit_code": completed.returncode,
            "stderr": completed.stderr.decode("utf-8", "replace").strip(),
        }
    entries = parse_null_config(completed.stdout)
    expected_remaining = [
        remote
        for remote in repository.get("remotes", [])
        if not remote.get("matches_target")
    ]
    current_remote_sections = sorted(
        {section for key, _ in entries if (section := remote_section(key)) is not None}
    )
    return {
        "read_succeeded": True,
        "entry_count": len(entries),
        "config_listing_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "target_remote_sections": target_remote_sections(entries, target_marker),
        "current_remote_sections": current_remote_sections,
        "expected_remaining_remote_sections": sorted(
            remote["section"] for remote in expected_remaining
        ),
        "remaining_remote_sections_match_inventory": current_remote_sections
        == sorted(remote["section"] for remote in expected_remaining),
    }


def refs_evidence(repository: dict[str, Any]) -> dict[str, Any]:
    arguments = [
        "git",
        f"--git-dir={repository['common_git_dir']}",
        "for-each-ref",
        "--format=%(refname)%00%(objectname)%00%(symref)",
    ]
    completed = run(arguments)
    if completed.returncode != 0:
        return {
            "read_succeeded": False,
            "exit_code": completed.returncode,
            "stderr": completed.stderr.decode("utf-8", "replace").strip(),
        }
    return {
        "read_succeeded": True,
        "count": len(completed.stdout.splitlines()),
        "sha256": hashlib.sha256(completed.stdout).hexdigest(),
    }


def nearby_git_metadata(common_git_dir: Path, config_path: Path) -> dict[str, Any]:
    selected_names = (
        "HEAD",
        "index",
        "packed-refs",
        "ORIG_HEAD",
        "FETCH_HEAD",
        "logs",
        "objects",
        "refs",
    )
    selected: list[dict[str, Any]] = []
    for name in selected_names:
        path = common_git_dir / name
        if path.exists() or path.is_symlink():
            selected.append(metadata(path))

    direct_children: list[dict[str, Any]] = []
    for path in sorted(common_git_dir.iterdir()):
        if path == config_path or path.name.endswith(".lock"):
            continue
        try:
            direct_children.append(metadata(path))
        except FileNotFoundError:
            continue
    group_distribution = Counter(
        (item["gid"], item["group"]) for item in direct_children
    )
    owner_distribution = Counter(
        (item["uid"], item["user"]) for item in direct_children
    )
    mode_distribution = Counter(item["mode_octal"] for item in direct_children)
    dominant_group = group_distribution.most_common(1)[0] if group_distribution else None
    dominant_owner = owner_distribution.most_common(1)[0] if owner_distribution else None
    return {
        "selected_entries": selected,
        "direct_child_count_excluding_config_and_locks": len(direct_children),
        "direct_child_group_distribution": [
            {"gid": key[0], "group": key[1], "count": count}
            for key, count in group_distribution.most_common()
        ],
        "direct_child_owner_distribution": [
            {"uid": key[0], "user": key[1], "count": count}
            for key, count in owner_distribution.most_common()
        ],
        "direct_child_mode_distribution": [
            {"mode": key, "count": count}
            for key, count in mode_distribution.most_common()
        ],
        "dominant_group": (
            {
                "gid": dominant_group[0][0],
                "group": dominant_group[0][1],
                "count": dominant_group[1],
            }
            if dominant_group
            else None
        ),
        "dominant_owner": (
            {
                "uid": dominant_owner[0][0],
                "user": dominant_owner[0][1],
                "count": dominant_owner[1],
            }
            if dominant_owner
            else None
        ),
    }


def inventory_config_cohort(document: dict[str, Any]) -> dict[str, Any]:
    groups: dict[str, Counter[tuple[str, int, str | None, int, str | None]]] = {
        "targeted": Counter(),
        "non_targeted": Counter(),
    }
    missing: list[str] = []
    for repository in document["repositories"]:
        config_path = Path(repository["config_path"])
        try:
            value = metadata(config_path)
        except FileNotFoundError:
            missing.append(repository["id"])
            continue
        label = (
            "targeted"
            if any(remote.get("matches_target") for remote in repository.get("remotes", []))
            else "non_targeted"
        )
        groups[label][
            (
                value["mode_octal"],
                value["uid"],
                value["user"],
                value["gid"],
                value["group"],
            )
        ] += 1
    return {
        label: [
            {
                "mode": key[0],
                "uid": key[1],
                "user": key[2],
                "gid": key[3],
                "group": key[4],
                "count": count,
            }
            for key, count in counter.most_common()
        ]
        for label, counter in groups.items()
    } | {"missing_repository_ids": missing}


def command_identity() -> dict[str, Any]:
    old_umask = os.umask(0)
    os.umask(old_umask)
    return {
        "euid": os.geteuid(),
        "user": user_name(os.geteuid()),
        "egid": os.getegid(),
        "group": group_name(os.getegid()),
        "supplementary_gids": list(os.getgroups()),
        "supplementary_groups": [group_name(gid) for gid in os.getgroups()],
        "umask_octal": f"0o{old_umask:04o}",
        "git_version": run(["git", "--version"], check=True)
        .stdout.decode("utf-8", "replace")
        .strip(),
    }


def resolve_scratchpad_root(path: Path) -> Path:
    """Resolve and create a fixture root beneath a `.scratchpad/` component."""

    scratchpad_root = path.expanduser().resolve()
    if ".scratchpad" not in scratchpad_root.parts:
        raise InvestigationError(
            "fixture output location check failed; "
            "condition=fixture root is beneath a canonical repository .scratchpad; "
            f"expected=path containing '.scratchpad'; received={scratchpad_root}"
        )
    scratchpad_root.mkdir(parents=True, exist_ok=True)
    return scratchpad_root


def chmod_and_optional_chgrp(path: Path, mode: int, gid: int | None) -> str | None:
    os.chmod(path, mode)
    if gid is None or path.stat().st_gid == gid:
        return None
    if os.geteuid() == 0 or gid in os.getgroups() or gid == os.getegid():
        os.chown(path, -1, gid)
        return None
    return (
        "fixture group setup check failed; condition=process may assign requested GID; "
        f"expected=euid 0 or membership in gid {gid}; "
        f"received=euid {os.geteuid()}, egid {os.getegid()}, groups {os.getgroups()}"
    )


def one_mode_experiment(
    fixture_root: Path,
    *,
    number: int,
    mode: int,
    parent_mode: int,
    desired_gid: int | None,
    target_value: str,
) -> dict[str, Any]:
    repository = fixture_root / f"mode-{number:04d}-{mode:04o}"
    run(
        ["git", "init", "--quiet", "--initial-branch=main", str(repository)],
        check=True,
    )
    config_path = repository / ".git" / "config"
    parent_path = config_path.parent
    group_setup_error = chmod_and_optional_chgrp(
        parent_path, parent_mode, desired_gid
    )
    run(
        [
            "git",
            "-C",
            str(repository),
            "config",
            "--local",
            "remote.origin.url",
            target_value,
        ],
        check=True,
    )
    config_group_error = chmod_and_optional_chgrp(config_path, mode, desired_gid)
    before = metadata(config_path)
    completed = run(
        [
            "git",
            "-C",
            str(repository),
            "config",
            "--local",
            "--remove-section",
            "remote.origin",
        ]
    )
    after = metadata(config_path) if config_path.exists() else None
    observed_changes: dict[str, dict[str, Any]] = {}
    if after is not None:
        for field in ("mode_octal", "uid", "gid"):
            if before[field] != after[field]:
                observed_changes[field] = {
                    "before": before[field],
                    "after": after[field],
                }
    return {
        "candidate_mode": f"0o{mode:04o}",
        "desired_gid": desired_gid,
        "group_setup_error": group_setup_error,
        "config_group_setup_error": config_group_error,
        "command": [
            "git",
            "-C",
            str(repository),
            "config",
            "--local",
            "--remove-section",
            "remote.origin",
        ],
        "exit_code": completed.returncode,
        "stderr": completed.stderr.decode("utf-8", "replace").strip(),
        "command_check": {
            "condition": "Git config removal command exits zero",
            "expected": 0,
            "received": completed.returncode,
            "passed": completed.returncode == 0,
        },
        "metadata_acceptance_gate": False,
        "before": tuple_from_metadata(before),
        "after": tuple_from_metadata(after) if after is not None else None,
        "observed_metadata_changes": observed_changes,
    }


def mode_experiments(
    *,
    scratchpad_root: Path,
    current_config: dict[str, Any],
    parent: dict[str, Any],
    nearby: dict[str, Any],
    cohort: dict[str, Any],
    target_value: str,
) -> list[dict[str, Any]]:
    modes: set[int] = {
        0o600,
        0o640,
        0o644,
        0o660,
        0o664,
        0o666,
        0o700,
        0o744,
        0o755,
        0o2644,
        0o2664,
        0o4644,
    }
    modes.add(int(current_config["mode_octal"], 8))
    for label in ("targeted", "non_targeted"):
        for item in cohort[label]:
            modes.add(int(item["mode"], 8))
    dominant_group = nearby.get("dominant_group")
    desired_gid = dominant_group["gid"] if dominant_group else current_config["gid"]
    parent_mode = int(parent["mode_octal"], 8)
    output: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(
        prefix="git-config-metadata-investigation-",
        dir=scratchpad_root,
    ) as temporary:
        fixture_root = Path(temporary)
        for number, mode in enumerate(sorted(modes), start=1):
            output.append(
                one_mode_experiment(
                    fixture_root,
                    number=number,
                    mode=mode,
                    parent_mode=parent_mode,
                    desired_gid=desired_gid,
                    target_value=target_value,
                )
            )
    return output


def derive_findings(
    *,
    current: dict[str, Any],
    parent: dict[str, Any],
    nearby: dict[str, Any],
    identity: dict[str, Any],
    experiments: list[dict[str, Any]],
    fixture_device_matches_config: bool,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    dominant_group = nearby.get("dominant_group")
    findings.append(
        {
            "status": "scope-boundary",
            "finding": (
                "Config mode, UID, GID, inode, and timestamps are diagnostic metadata, "
                "not acceptance conditions. This investigation does not require their "
                "preservation and cannot fail because they differ."
            ),
        }
    )
    findings.append(
        {
            "status": "parameter-parity",
            "finding": (
                "The scratchpad fixture and selected production config are on the same "
                "filesystem device."
                if fixture_device_matches_config
                else "The scratchpad fixture and selected production config are on "
                "different filesystem devices; experiment results do not establish "
                "same-filesystem production behavior."
            ),
        }
    )
    if dominant_group and current["gid"] != dominant_group["gid"]:
        findings.append(
            {
                "status": "current-evidence",
                "finding": (
                    f"The current config group is {current['gid']} ({current['group']}), "
                    f"while the dominant group among neighboring untouched Git metadata "
                    f"is {dominant_group['gid']} ({dominant_group['group']}) across "
                    f"{dominant_group['count']} direct entries."
                ),
            }
        )
    if current["gid"] == identity["egid"]:
        findings.append(
            {
                "status": "current-evidence",
                "finding": (
                    "The current config group equals the executing process effective "
                    "group, which is the group assigned to a newly created lock file "
                    "when the parent directory does not impose setgid inheritance."
                ),
            }
        )
    parent_mode = int(parent["mode_octal"], 8)
    findings.append(
        {
            "status": "proven",
            "finding": (
                f"The config parent mode is {parent['mode_octal']}; setgid inheritance "
                f"is {'enabled' if parent_mode & stat.S_ISGID else 'not enabled'}."
            ),
        }
    )
    changed_experiments = [
        item for item in experiments if item["observed_metadata_changes"]
    ]
    fields = Counter(
        field
        for item in changed_experiments
        for field in item["observed_metadata_changes"]
    )
    findings.append(
        {
            "status": "controlled-reproduction",
            "finding": (
                f"The exact Git command changed metadata in {len(changed_experiments)} "
                f"of {len(experiments)} tested pre-metadata states; changed-field "
                f"counts were {dict(fields)}."
            ),
        }
    )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Investigate Git config metadata behavior as non-gating observability."
        )
    )
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--target-marker", required=True)
    parser.add_argument("--fixture-remote-value")
    parser.add_argument("--scratchpad-root", type=Path, required=True)
    arguments = parser.parse_args()

    index_path = arguments.index.resolve()
    document = load_inventory(index_path)
    repository = find_repository(document, arguments.repository)
    config_path = Path(repository["config_path"])
    common_git_dir = Path(repository["common_git_dir"])
    scratchpad_root = resolve_scratchpad_root(arguments.scratchpad_root)
    current = metadata(config_path)
    parent = metadata(config_path.parent)
    nearby = nearby_git_metadata(common_git_dir, config_path)
    cohort = inventory_config_cohort(document)
    identity = command_identity()
    fixture_remote_value = arguments.fixture_remote_value or arguments.target_marker
    fixture_device = scratchpad_root.stat().st_dev
    fixture_device_matches_config = fixture_device == current["device"]

    print(
        "investigation: running disposable scratchpad metadata experiments",
        file=sys.stderr,
        flush=True,
    )
    experiments = mode_experiments(
        scratchpad_root=scratchpad_root,
        current_config=current,
        parent=parent,
        nearby=nearby,
        cohort=cohort,
        target_value=fixture_remote_value,
    )

    report = {
        "schema_version": 1,
        "production_writes_performed": False,
        "disposable_fixture_root_removed_before_exit": True,
        "metadata_acceptance_gate": False,
        "index_path": str(index_path),
        "target_marker": arguments.target_marker,
        "inventory_fingerprint_sha256": document.get(
            "inventory_fingerprint_sha256"
        ),
        "repository": {
            "id": repository["id"],
            "path": repository["path"],
            "kind": repository["kind"],
            "common_git_dir": repository["common_git_dir"],
            "config_path": repository["config_path"],
            "original_target_sections": [
                remote["section"]
                for remote in repository.get("remotes", [])
                if remote.get("matches_target")
            ],
        },
        "recorded_failure": parse_failure_message(repository),
        "current_config_metadata": current,
        "current_config_tuple": tuple_from_metadata(current),
        "config_parent_metadata": parent,
        "executing_identity": identity,
        "nearby_git_metadata": nearby,
        "inventory_config_cohort": cohort,
        "current_config_semantics": current_config_semantics(
            repository, arguments.target_marker
        ),
        "current_refs_evidence": refs_evidence(repository),
        "fixture_parameter_comparison": {
            "scratchpad_root": str(scratchpad_root),
            "scratchpad_device": fixture_device,
            "production_config_device": current["device"],
            "same_filesystem_device": fixture_device_matches_config,
            "claim_boundary": (
                "experiment results establish same-filesystem behavior"
                if fixture_device_matches_config
                else "experiment results do not establish same-filesystem production behavior"
            ),
        },
        "controlled_scratchpad_experiments": experiments,
        "findings": derive_findings(
            current=current,
            parent=parent,
            nearby=nearby,
            identity=identity,
            experiments=experiments,
            fixture_device_matches_config=fixture_device_matches_config,
        ),
        "required_failure_contract": {
            "required_fields": [
                "event",
                "repository_id",
                "repository_path",
                "config_path",
                "condition",
                "expected",
                "received",
                "mismatched_fields",
                "effect_state",
            ],
            "rule": (
                "Only user-defined acceptance conditions may fail a run. Every failure "
                "must name the checked condition and exact expected and received values."
            ),
        },
    }
    print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InvestigationError as error:
        print(f"INVESTIGATION_ERROR: {error}", file=sys.stderr, flush=True)
        raise SystemExit(2)
