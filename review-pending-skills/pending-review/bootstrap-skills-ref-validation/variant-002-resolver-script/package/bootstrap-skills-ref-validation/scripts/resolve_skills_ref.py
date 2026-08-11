#!/usr/bin/env python3
"""Resolve skills-ref CLI, module, pinned source, and helper states without mutation."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import stat
import sys
import tomllib
from pathlib import Path
from typing import Any


def display_path(path: Path | str | None) -> str | None:
    if path is None:
        return None
    resolved = Path(path).resolve()
    home = Path.home().resolve()
    try:
        relative = resolved.relative_to(home)
    except ValueError:
        return resolved.as_posix()
    return "~" if not relative.parts else f"~/{relative.as_posix()}"


def load_metadata(source: Path) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    pyproject = source / "pyproject.toml"
    if not pyproject.is_file():
        return {}, ["pyproject.toml is missing"]
    try:
        document = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        return {}, [str(error)]
    project = document.get("project")
    if not isinstance(project, dict):
        errors.append("[project] metadata is missing")
        project = {}
    build_system = document.get("build-system")
    if not isinstance(build_system, dict):
        build_system = {}
    metadata = {
        "name": project.get("name"),
        "version": project.get("version"),
        "dependencies": project.get("dependencies", []),
        "build_backend": build_system.get("build-backend"),
    }
    if not isinstance(metadata["name"], str) or not metadata["name"]:
        errors.append("project.name is missing")
    if not isinstance(metadata["version"], str) or not metadata["version"]:
        errors.append("project.version is missing")
    if not isinstance(metadata["dependencies"], list):
        errors.append("project.dependencies must be an array")
    return metadata, errors


def helper_states(source: Path) -> list[dict[str, Any]]:
    scripts = source / "scripts"
    if not scripts.is_dir():
        return []
    states: list[dict[str, Any]] = []
    for helper in sorted(scripts.glob("*.py")):
        mode = helper.stat().st_mode
        executable = bool(mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
        states.append(
            {
                "path": display_path(helper),
                "executable": executable,
                "recommended_invocation": [sys.executable, display_path(helper)],
            }
        )
    return states


def resolve(repo: Path, source_arg: Path, cli_name: str, module_name: str) -> tuple[int, dict[str, Any]]:
    repo = repo.resolve()
    source = (repo / source_arg).resolve() if not source_arg.is_absolute() else source_arg.resolve()
    try:
        source.relative_to(repo)
    except ValueError:
        return 2, {"schema_version": 1, "status": "invalid-source", "errors": ["source escapes repository"]}

    cli_path = shutil.which(cli_name)
    cli = {"name": cli_name, "state": "present" if cli_path else "missing", "path": display_path(cli_path)}

    module: dict[str, Any] = {"name": module_name, "state": "missing", "origin": None}
    try:
        spec = importlib.util.find_spec(module_name)
    except (ImportError, AttributeError, ValueError) as error:
        spec = None
        module = {"name": module_name, "state": "error", "origin": None, "error": str(error)}
    if spec is not None:
        origin = spec.origin
        if origin is None and spec.submodule_search_locations:
            origin = next(iter(spec.submodule_search_locations), None)
        module = {"name": module_name, "state": "present", "origin": display_path(origin)}

    source_state = "present" if source.is_dir() else "missing"
    metadata: dict[str, Any] = {}
    metadata_errors: list[str] = []
    if source_state == "present":
        metadata, metadata_errors = load_metadata(source)
        if metadata_errors:
            source_state = "invalid"

    provenance = "not-installed"
    if module["state"] == "present":
        origin_value = module.get("origin")
        if isinstance(origin_value, str):
            origin_expanded = Path(origin_value.replace("~/", str(Path.home()) + os.sep)) if origin_value.startswith("~/") else Path(origin_value)
            try:
                origin_expanded.resolve().relative_to(source)
                provenance = "matches-pinned-source"
            except ValueError:
                provenance = "different-origin"
        else:
            provenance = "unresolved"
    elif module["state"] == "error":
        provenance = "unresolved"

    install_plan = None
    if source_state == "present":
        install_plan = [sys.executable, "-m", "pip", "install", "-e", display_path(source)]
    report = {
        "schema_version": 1,
        "status": "resolved" if source_state == "present" else "incomplete",
        "repository": display_path(repo),
        "cli": cli,
        "module": module,
        "source": {"state": source_state, "path": display_path(source)},
        "metadata": metadata,
        "metadata_errors": metadata_errors,
        "provenance": provenance,
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
    parser.add_argument("--json", action="store_true", help="Retained for explicit machine-readable invocation; output is always JSON.")
    args = parser.parse_args(argv)
    code, report = resolve(args.repo, args.source, args.cli_name, args.module_name)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
