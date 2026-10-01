#!/usr/bin/env python3
"""Compare committed upstream packages with archived bases and canonical ports.

No command patches ported skills, pulls Git, installs packages, or changes links.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA = 1
NAME = re.compile(r"ripwire-[a-z0-9]+(?:-[a-z0-9]+)*\Z")
STATE_RELATIVE = Path("manage-ripwire-skills/assets/upstream-baseline.json")


class StateError(Exception):
    @property
    def details(self) -> dict[str, Any]:
        condition, expected, received = self.args
        return {"condition": condition, "expected": expected, "received": received}


def normalized(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace(str(Path.home()), "~")
    if isinstance(value, list):
        return [normalized(item) for item in value]
    if isinstance(value, dict):
        return {key: normalized(item) for key, item in value.items()}
    return value


def signature(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def git(repo: Path, *args: str) -> bytes:
    command = ["git", "-C", str(repo), *args]
    result = subprocess.run(command, capture_output=True)
    if result.returncode:
        raise StateError("Git read succeeds", 0, {"exit_code": result.returncode,
                         "command": command, "stdout": result.stdout.decode(errors="replace"),
                         "stderr": result.stderr.decode(errors="replace")})
    return result.stdout


def file_record(body: bytes, executable: bool = False) -> dict[str, Any]:
    return {"sha256": hashlib.sha256(body).hexdigest(), "executable": executable,
            "content_base64": base64.b64encode(body).decode("ascii")}


def file_summary(record: dict[str, Any] | None) -> dict[str, Any] | None:
    return None if record is None else {key: record[key] for key in ("sha256", "executable")}


def package_signature(files: dict[str, Any]) -> str:
    return signature({key: file_summary(value) for key, value in files.items()})


def valid_relative(path: str) -> bool:
    if not isinstance(path, str):
        return False
    p = PurePosixPath(path)
    return bool(p.parts) and not p.is_absolute() and ".." not in p.parts and "\\" not in path


def committed_tree(repo: Path, oid: str) -> dict[str, tuple[str, str, str]]:
    listing = git(repo, "ls-tree", "-rz", "--full-tree", oid)
    entries = {}
    for raw in listing.split(b"\0"):
        if not raw:
            continue
        header, raw_path = raw.split(b"\t", 1)
        mode, kind, blob = header.decode().split()
        entries[raw_path.decode()] = (mode, kind, blob)
    return entries


def upstream_file(repo: Path, path: str, entry: tuple[str, str, str]) -> dict[str, Any]:
    mode, kind, blob = entry
    if mode not in {"100644", "100755"} or kind != "blob":
        raise StateError("upstream resources are regular files", "100644/100755 blob", {"path": path, "mode": mode})
    return file_record(git(repo, "cat-file", "blob", blob), mode == "100755")


def upstream_package_files(repo: Path, entries: dict[str, Any], name: str) -> dict[str, Any]:
    prefix = "skills/" + name + "/"
    files = {}
    for path, entry in entries.items():
        if not path.startswith(prefix):
            continue
        relative = path[len(prefix):]
        if not valid_relative(relative):
            raise StateError("upstream resource path is contained", "package-relative path", relative)
        files[relative] = upstream_file(repo, path, entry)
    return files


def validate_identity(name: str, record: dict[str, Any]) -> None:
    skill = base64.b64decode(record["content_base64"]).decode()
    frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", skill, re.DOTALL)
    if frontmatter is None:
        raise StateError("upstream skill has frontmatter", "opening and closing --- lines", name)
    declared = re.search(r"(?m)^name:\s*[\"']?([a-z0-9-]+)[\"']?\s*$", frontmatter.group(1))
    if declared is None or declared.group(1) != name:
        raise StateError("upstream package identity matches", name, declared.group(1) if declared else None)


def committed_packages(repo: Path, ref: str = "HEAD") -> tuple[str, dict[str, Any]]:
    oid = git(repo, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()
    entries = committed_tree(repo, oid)
    names = sorted({PurePosixPath(path).parts[1] for path in entries
                    if len(PurePosixPath(path).parts) == 3 and path.startswith("skills/")
                    and path.endswith("/SKILL.md") and NAME.fullmatch(PurePosixPath(path).parts[1])})
    if not names:
        raise StateError("committed upstream skills exist", "immediate skills/ripwire-*/SKILL.md packages", [])
    notices = {name + ".upstream": upstream_file(repo, name, entries[name])
               for name in ("LICENSE", "NOTICE") if name in entries}
    packages = {}
    for name in names:
        files = upstream_package_files(repo, entries, name)
        validate_identity(name, files["SKILL.md"])
        files.update(notices)
        packages[name] = {"upstream_oid": oid, "files": files}
    return oid, packages


def local_files(root: Path, name: str) -> dict[str, Any]:
    package = root / name
    if not package.exists():
        return {}
    if package.is_symlink() or not package.is_dir():
        raise StateError("canonical package is a real directory", "directory", str(package))
    files = {}
    for path in sorted(package.rglob("*")):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise StateError("canonical resource is contained", "regular file/directory", str(path))
        if path.is_file():
            files[path.relative_to(package).as_posix()] = file_record(path.read_bytes(), bool(path.stat().st_mode & 0o111))
    return files


def validate_archived_file(relative: str, record: Any) -> None:
    if not isinstance(record, dict):
        raise StateError("archived file has a record", "object", relative)
    try:
        body = base64.b64decode(record["content_base64"], validate=True)
        actual = hashlib.sha256(body).hexdigest()
    except (KeyError, ValueError, TypeError) as error:
        raise StateError("archived bytes are valid", "base64 bytes and hash", relative) from error
    if not valid_relative(relative) or actual != record.get("sha256") or type(record.get("executable")) is not bool:
        raise StateError("archived bytes match their record", record.get("sha256"), {"path": relative, "sha256": actual})


def validate_archived_package(name: str, package: Any) -> None:
    if not NAME.fullmatch(name) or not isinstance(package, dict):
        raise StateError("baseline package is named", "ripwire package object", name)
    files = package.get("files")
    oid = package.get("upstream_oid")
    if not isinstance(files, dict) or not isinstance(oid, str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", oid):
        raise StateError("baseline package has files and provenance", "files object and commit ID", name)
    tombstone = package.get("upstream_removed") is True and not files
    if "SKILL.md" not in files and not tombstone:
        raise StateError("baseline package is complete", "SKILL.md or upstream-removal record", name)
    for relative, record in files.items():
        validate_archived_file(relative, record)


def read_state(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise StateError("baseline is a regular canonical file", "non-symlink", str(path))
    try:
        state = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise StateError("baseline is readable JSON", "schema 1 baseline", str(error)) from error
    if not isinstance(state, dict) or state.get("schema_version") != SCHEMA or not isinstance(state.get("packages"), dict):
        raise StateError("baseline schema is supported", SCHEMA, state)
    for name, package in state["packages"].items():
        validate_archived_package(name, package)
    return state


def atomic_json(path: Path, value: dict[str, Any], scratch: Path) -> None:
    scratch.mkdir(parents=True, exist_ok=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="ripwire-state-", suffix=".json", dir=scratch)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(normalized(value), stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def state_path(skills_root: Path) -> Path:
    path = skills_root / STATE_RELATIVE
    if not path.parent.resolve().is_relative_to(skills_root.resolve()):
        raise StateError("baseline stays in canonical repository", str(skills_root), str(path.parent.resolve()))
    return path


def initialize(skills_root: Path, upstream: Path, ref: str) -> dict[str, Any]:
    path = state_path(skills_root)
    if path.exists() or path.is_symlink():
        raise StateError("initial baseline is absent", "absent", str(path))
    oid, packages = committed_packages(upstream, ref)
    state = {"schema_version": SCHEMA, "upstream_repo": normalized(str(upstream)), "packages": packages}
    atomic_json(path, state, skills_root / ".scratchpad/manage-ripwire-skills")
    read_state(path)
    return {"status": "initialized", "upstream_oid": oid, "packages": len(packages)}


def upstream_changes(base: dict, new: dict, local: dict) -> list[dict]:
    changes = []
    for relative in sorted(base.keys() | new.keys()):
        b, u, l = (file_summary(files.get(relative)) for files in (base, new, local))
        if b == u:
            continue
        kind = "both-changed"
        if l == u:
            kind = "already-equal"
        elif l == b:
            kind = "upstream-only"
        changes.append({"path": relative, "base": b, "upstream": u, "canonical": l, "kind": kind})
    return changes


def review_status(name: str, archived: dict, current: dict, local: dict, changes: list) -> str:
    if name not in archived:
        return "new-upstream-package"
    if name not in current:
        if archived[name].get("upstream_removed") is True:
            return "upstream-current"
        return "removed-upstream-package"
    if "SKILL.md" not in local:
        return "canonical-missing"
    if changes:
        return "review-required"
    return "upstream-current"


def compare(skills_root: Path, upstream: Path, ref: str) -> dict[str, Any]:
    state = read_state(state_path(skills_root))
    archived = state["packages"]
    oid, current = committed_packages(upstream, ref)
    rows = []
    for name in sorted(archived.keys() | current.keys()):
        base = archived.get(name, {}).get("files", {})
        new = current.get(name, {}).get("files", {})
        local = local_files(skills_root, name)
        changes = upstream_changes(base, new, local)
        status = review_status(name, archived, current, local, changes)
        rows.append({"name": name, "status": status, "base_oid": state["packages"].get(name, {}).get("upstream_oid"),
                     "changes": changes, "upstream_signature": package_signature(new),
                     "canonical_signature": package_signature(local),
                     "upstream_removed": name not in current,
                     "local_customized": package_signature(local) != package_signature(base)})
    return {"schema_version": SCHEMA, "baseline_signature": signature(state), "upstream_oid": oid,
            "ref": ref, "skills_root": normalized(str(skills_root)), "upstream_repo": normalized(str(upstream)),
            "status": "review-required" if any(r["status"] != "upstream-current" for r in rows) else "upstream-current",
            "meaning": "Committed upstream definition drift only; this does not prove semantic equivalence or runtime acceptance.",
            "packages": rows}


def review_units(decisions: Any, changed: dict) -> dict:
    if not isinstance(decisions, dict) or not isinstance(decisions.get("packages"), list):
        raise StateError("review decisions have package rows", "object with packages array", decisions)
    resolutions = decisions["packages"]
    by_name = {}
    for row in resolutions:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise StateError("review unit has an identity", "object with name string", row)
        name = row["name"]
        if name in by_name:
            raise StateError("review identities are unique", "one row per package", name)
        choice, reason = row.get("disposition"), row.get("reason")
        if not isinstance(choice, str) or choice not in {"accepted", "deferred"} or not isinstance(reason, str) or not reason.strip():
            raise StateError("disposition is explicit", "accepted/deferred with reason string", row)
        by_name[name] = row
    if set(by_name) != set(changed):
        raise StateError("every changed package has one disposition", sorted(changed), sorted(by_name))
    return by_name


def accepted_evidence(skills_root: Path, evidence: Any) -> list[str]:
    if not isinstance(evidence, list) or not evidence:
        raise StateError("accepted review names canonical evidence", "nonempty relative file list", evidence)
    for relative in evidence:
        if not valid_relative(relative):
            raise StateError("evidence path is relative", "canonical-relative file path", relative)
        path = skills_root / relative
        if not path.is_file() or not path.resolve().is_relative_to(skills_root.resolve()):
            raise StateError("evidence file exists canonically", "contained canonical file", relative)
    return evidence


def reviewed_baseline(skills_root: Path, name: str, row: dict, resolution: dict, new_base: dict) -> dict:
    if row["status"] == "canonical-missing":
        raise StateError("missing canonical package is deferred", "deferred until repaired", name)
    if row["status"] != "removed-upstream-package" and "SKILL.md" not in local_files(skills_root, name):
        raise StateError("accepted package exists canonically", "SKILL.md", name)
    evidence = accepted_evidence(skills_root, resolution.get("evidence"))
    return new_base | {"review": {"reason": resolution["reason"], "evidence": evidence,
                                 "canonical_signature": row["canonical_signature"]}}


def acknowledge(skills_root: Path, upstream: Path, report: dict, decisions: dict) -> dict:
    if not isinstance(report, dict) or not isinstance(report.get("ref"), str):
        raise StateError("comparison report has a revision", "check report object with ref string", report)
    path = state_path(skills_root)
    lock = skills_root / ".scratchpad/manage-ripwire-skills/acknowledge.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise StateError("baseline writer lock is absent", "absent", str(lock)) from error
    try:
        os.close(fd)
        fresh = compare(skills_root, upstream, report["ref"])
        if fresh != report:
            raise StateError("review report inputs are current", signature(report), signature(fresh))
        changed = {row["name"]: row for row in report["packages"] if row["status"] != "upstream-current"}
        by_name = review_units(decisions, changed)
        state = read_state(path)
        _, current = committed_packages(upstream, report["upstream_oid"])
        accepted, deferred = [], []
        for name, resolution in by_name.items():
            if resolution["disposition"] == "deferred":
                deferred.append(name)
                continue
            new_base = current.get(name, {"upstream_oid": report["upstream_oid"], "files": {}, "upstream_removed": True})
            state["packages"][name] = reviewed_baseline(skills_root, name, changed[name], resolution, new_base)
            accepted.append(name)
        if accepted:
            atomic_json(path, state, skills_root / ".scratchpad/manage-ripwire-skills")
            read_state(path)
        return {"status": "deferred" if deferred and not accepted else "partially-acknowledged" if deferred else "acknowledged", "accepted": accepted,
                "deferred": deferred, "canonical_files_written": False,
                "baseline_written": bool(accepted),
                "meaning": "Records reviewed upstream bases; does not certify agent review, runtime acceptance, or user authority."}
    finally:
        lock.unlink()


def report_destination(args: argparse.Namespace, root: Path, upstream: Path) -> Path | None:
    if args.output is None:
        return None
    destination = args.output.expanduser().resolve()
    if not destination.is_relative_to(root / ".scratchpad"):
        raise StateError("report is in canonical scratch", str(root / ".scratchpad"), str(destination))
    if not destination.exists():
        return destination
    if not args.replace_report or args.action != "check":
        raise StateError("report output is absent or replacement is explicit", "new path or --replace-report for check", str(destination))
    previous = json.loads(destination.read_text())
    if not isinstance(previous, dict) or previous.get("schema_version") != SCHEMA or previous.get("skills_root") != normalized(str(root)) or previous.get("upstream_repo") != normalized(str(upstream)) or not isinstance(previous.get("packages"), list):
        raise StateError("replacement is this manager's report for these roots", "matching check report", str(destination))
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("initialize", "check", "acknowledge"))
    parser.add_argument("--skills-root", type=Path, default=Path.home() / "agentic-skills")
    parser.add_argument("--upstream-repo", type=Path, default=Path.home() / "github-forks/ripwire")
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--replace-report", action="store_true", help="Replace this manager's existing check report at the named scratch path.")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--decisions", type=Path)
    args = parser.parse_args()
    root, upstream = args.skills_root.expanduser().resolve(), args.upstream_repo.expanduser().resolve()
    try:
        destination = report_destination(args, root, upstream)
        if args.action == "initialize":
            result = initialize(root, upstream, args.ref)
        elif args.action == "check":
            result = compare(root, upstream, args.ref)
        else:
            if args.report is None or args.decisions is None:
                raise StateError("acknowledgement inputs exist", "--report and --decisions", None)
            result = acknowledge(root, upstream, json.loads(args.report.expanduser().read_text()), json.loads(args.decisions.expanduser().read_text()))
        if destination is not None:
            atomic_json(destination, result, root / ".scratchpad/manage-ripwire-skills")
        print(json.dumps(normalized(result), indent=2, sort_keys=True))
        return 0
    except (StateError, OSError, ValueError, KeyError) as error:
        details = error.details if isinstance(error, StateError) else {"condition": "valid input", "expected": "readable valid inputs", "received": str(error)}
        print(json.dumps(normalized({"status": "failed", **details}), indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
