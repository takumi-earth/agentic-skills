#!/usr/bin/env python3
"""Inspect validator discovery, pinned provenance, and distribution versions."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import shutil
import stat
import sys
import tomllib
from pathlib import Path
from typing import Any


def present(value: Any) -> Any:
    if isinstance(value, str):
        home = str(Path.home())
        return "~" if value == home else value.replace(home + "/", "~/")
    if isinstance(value, list):
        return [present(item) for item in value]
    if isinstance(value, dict):
        return {key: present(item) for key, item in value.items()}
    return value


def load_metadata(source: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        document = tomllib.loads((source / "pyproject.toml").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return {}, [str(error)]
    project = document.get("project")
    if not isinstance(project, dict):
        return {}, ["[project] metadata is missing"]
    build_system = document.get("build-system", {})
    if not isinstance(build_system, dict):
        return {}, ["[build-system] metadata must be a table"]
    metadata = {
        "name": project.get("name"),
        "version": project.get("version"),
        "dependencies": project.get("dependencies", []),
        "build_backend": build_system.get("build-backend"),
    }
    errors: list[str] = []
    for field in ("name", "version"):
        if not isinstance(metadata[field], str) or not metadata[field].strip():
            errors.append(f"project.{field} must be a nonempty string")
    dependencies = metadata["dependencies"]
    if not isinstance(dependencies, list) or any(
        not isinstance(item, str) or not item.strip() for item in dependencies
    ):
        errors.append("project.dependencies must be a string array")
    return metadata, errors


def helper_states(source: Path) -> list[dict[str, Any]]:
    scripts = source / "scripts"
    if not scripts.is_dir():
        return []
    states: list[dict[str, Any]] = []
    for helper in sorted(scripts.glob("*.py")):
        resolved = helper.resolve()
        if not resolved.is_relative_to(source):
            states.append({"path": str(helper), "state": "outside-source"})
            continue
        try:
            mode = helper.stat().st_mode
            executable = bool(mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
        except OSError as error:
            states.append({"path": str(helper), "state": "error", "error": str(error)})
            continue
        states.append({
            "path": str(resolved),
            "state": "present",
            "executable": executable,
            "recommended_invocation": ["python3", str(resolved)],
        })
    return states


def discover_module(module_name: str) -> dict[str, Any]:
    report: dict[str, Any] = {
        "name": module_name, "state": "missing", "origin": None,
        "import_executed": False,
    }
    try:
        spec = importlib.util.find_spec(module_name)
    except (ImportError, AttributeError, ValueError) as error:
        report.update({"state": "error", "error": str(error)})
        return report
    if spec is None:
        return report
    origin = spec.origin
    if origin is None and spec.submodule_search_locations:
        origin = next(iter(spec.submodule_search_locations), None)
    if origin is not None and origin not in {"built-in", "frozen"}:
        origin = str(Path(origin).resolve())
    report.update({"state": "discoverable", "origin": origin})
    return report


def installed_distribution(name: str | None) -> dict[str, Any]:
    report: dict[str, Any] = {"name": name, "state": "unknown", "version": None}
    if name is None:
        return report
    try:
        distribution = importlib.metadata.distribution(name)
    except importlib.metadata.PackageNotFoundError:
        report["state"] = "missing"
        return report
    except (OSError, ValueError) as error:
        report.update({"state": "error", "error": str(error)})
        return report
    version = distribution.version
    report.update({
        "state": "present" if isinstance(version, str) and version else "invalid",
        "version": version,
    })
    return report


def module_provenance(module: dict[str, Any], source: Path) -> str:
    if module["state"] == "missing":
        return "not-installed"
    origin = module.get("origin")
    if module["state"] != "discoverable" or origin in {None, "built-in", "frozen"}:
        return "unresolved"
    return "matches-pinned-source" if Path(origin).is_relative_to(source) else "different-origin"


def resolve(
    repo: Path,
    source_arg: Path,
    cli_name: str,
    module_name: str,
    distribution_name: str | None = None,
) -> tuple[int, dict[str, Any]]:
    if not module_name.isidentifier():
        return 2, {
            "status": "invalid-input",
            "errors": ["module-name must be a top-level Python identifier"],
        }
    repo = repo.expanduser().resolve()
    source_arg = source_arg.expanduser()
    source = (repo / source_arg).resolve()
    if not repo.is_dir() or not source.is_relative_to(repo):
        return 2, {
            "status": "invalid-source",
            "errors": ["repository must exist and source must resolve inside it"],
        }
    cli_path = shutil.which(cli_name)
    cli = {
        "name": cli_name, "state": "present" if cli_path else "missing",
        "path": str(Path(cli_path).resolve()) if cli_path else None,
    }
    module = discover_module(module_name)
    source_state = "present" if source.is_dir() else "missing"
    metadata: dict[str, Any] = {}
    metadata_errors: list[str] = []
    if source_state == "present":
        metadata, metadata_errors = load_metadata(source)
        if metadata_errors:
            source_state = "invalid"
    if distribution_name is None:
        name = metadata.get("name")
        distribution_name = name if isinstance(name, str) and name else None
    installed = installed_distribution(distribution_name)
    version_agreement = "unresolved"
    if source_state == "present" and installed["state"] == "present":
        version_agreement = "matches" if installed["version"] == metadata["version"] else "different"
    install_plan = None
    if source_state == "present":
        install_plan = ["python3", "-m", "pip", "install", "-e", str(source)]
    report = {
        "schema_version": 1,
        "status": "resolved" if source_state == "present" else "incomplete",
        "repository": str(repo),
        "cli": cli,
        "module": module,
        "source": {"state": source_state, "path": str(source)},
        "metadata": metadata,
        "metadata_errors": metadata_errors,
        "installed_distribution": installed,
        "provenance": module_provenance(module, source),
        "version_agreement": version_agreement,
        "helpers": helper_states(source) if source_state in {"present", "invalid"} else [],
        "install_plan": install_plan,
        "mutated_environment": False,
    }
    return 0, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--cli-name", default="skills-ref")
    parser.add_argument("--module-name", default="skills_ref")
    parser.add_argument("--distribution-name")
    args = parser.parse_args(argv)
    try:
        code, report = resolve(
            args.repo, args.source, args.cli_name, args.module_name, args.distribution_name,
        )
    except (OSError, ValueError) as error:
        code, report = 2, {"status": "discovery-error", "errors": [str(error)]}
    print(json.dumps(present(report), indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
