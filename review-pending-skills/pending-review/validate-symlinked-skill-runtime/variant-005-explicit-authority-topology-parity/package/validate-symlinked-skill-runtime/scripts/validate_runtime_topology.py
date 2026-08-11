#!/usr/bin/env python3
"""Validate a real stateful entry point across disposable deployment topologies."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Mapping


MODE = "explicit-authority-topology-parity"
NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def display(path: Path) -> str:
    """Render paths beneath the current home as `~/...`."""

    absolute = path.expanduser().absolute()
    home = Path.home().resolve(strict=False)
    try:
        relative = absolute.relative_to(home)
    except ValueError:
        return str(absolute)
    return "~" if relative == Path(".") else f"~/{relative.as_posix()}"


def normalize_error(error: Exception) -> str:
    """Normalize home paths in one stable diagnostic string."""

    return str(error).replace(str(Path.home().resolve(strict=False)), "~")


def relative_entry_point(value: str) -> str:
    """Require one canonical package-relative entry point."""

    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or ".." in path.parts or not path.parts:
        raise ValueError(f"entry point must be package-relative: {value!r}")
    return value


def explicit_directory(path: Path, name: str) -> Path:
    """Require one absolute existing directory authority."""

    candidate = path.expanduser()
    if not candidate.is_absolute():
        raise ValueError(f"{name} must be absolute")
    resolved = candidate.resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError(f"{name} must be an existing directory")
    return resolved


def resolve_runtime_root(
    explicit: Path | None,
    environ: Mapping[str, str],
) -> Path:
    """Use an explicit root or inherited `CODEX_HOME`, never package topology."""

    if explicit is not None:
        return explicit_directory(explicit, "runtime root")
    raw = environ.get("CODEX_HOME")
    if raw is None or not raw.strip():
        raise ValueError("runtime root requires --runtime-root or nonempty CODEX_HOME")
    return explicit_directory(Path(raw), "CODEX_HOME")


def parse_sibling(value: str) -> tuple[str, Path]:
    """Parse one declared `name=canonical-path` sibling dependency."""

    name, separator, raw_path = value.partition("=")
    if separator != "=" or NAME_RE.fullmatch(name) is None or not raw_path:
        raise ValueError(
            "sibling package must equal <package-name>=<canonical-package-path>"
        )
    return name, Path(raw_path)


def tree_digest(root: Path) -> str:
    """Hash paths, bytes, executable modes, and symlink targets."""

    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"tree root is not a real directory: {root}")
    entries: list[tuple[str, str, bytes]] = []
    for directory, names, filenames in os.walk(root, followlinks=False):
        parent = Path(directory)
        for name in [*names, *filenames]:
            path = parent / name
            relative = path.relative_to(root).as_posix()
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                entries.append((relative, "120000", os.readlink(path).encode()))
            elif stat.S_ISREG(metadata.st_mode):
                mode = "100755" if metadata.st_mode & stat.S_IXUSR else "100644"
                entries.append((relative, mode, path.read_bytes()))
            elif not stat.S_ISDIR(metadata.st_mode):
                raise ValueError(f"unsupported tree entry: {relative}")
    digest = hashlib.sha256()
    for relative, mode, payload in sorted(entries):
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(mode.encode())
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return digest.hexdigest()


def validate_layout(
    canonical_repository: Path,
    source_package: Path,
    siblings: list[tuple[str, Path]],
) -> tuple[Path, dict[str, Path]]:
    """Require the target and declared siblings as canonical immediate children."""

    repository = explicit_directory(canonical_repository, "canonical repository")
    source = explicit_directory(source_package, "source package")
    if source.parent != repository:
        raise ValueError("source package must be an immediate canonical repository child")
    packages = {source.name: source}
    for name, raw_path in siblings:
        if name in packages:
            raise ValueError(f"duplicate or target sibling name: {name}")
        sibling = explicit_directory(raw_path, f"sibling package {name}")
        if sibling.parent != repository or sibling.name != name:
            raise ValueError(
                f"sibling {name} must be the matching canonical repository child"
            )
        packages[name] = sibling
    return source, packages


def normalize_value(value: Any, replacements: list[tuple[str, str]]) -> Any:
    """Normalize only topology-specific package and task-output paths."""

    if isinstance(value, str):
        normalized = value
        for original, replacement in replacements:
            normalized = normalized.replace(original, replacement)
        return normalized
    if isinstance(value, list):
        return [normalize_value(item, replacements) for item in value]
    if isinstance(value, dict):
        return {
            str(key): normalize_value(item, replacements)
            for key, item in value.items()
            if key != "topology"
        }
    return value


def contained(path: Path, root: Path) -> bool:
    """Return whether a path remains beneath the selected disposable root."""

    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=True))
    except ValueError:
        return False
    return True


def build_fixture_repository(
    *,
    fixture_root: Path,
    mode: str,
    packages: dict[str, Path],
    include_siblings: bool,
    target_name: str,
) -> Path:
    """Build one copied or linked lexical repository fixture."""

    repository = fixture_root / f"{mode}-repository"
    repository.mkdir()
    selected = {
        name: path
        for name, path in packages.items()
        if include_siblings or name == target_name
    }
    for name, source in selected.items():
        destination = repository / name
        if mode == "copied":
            shutil.copytree(source, destination, symlinks=True)
        elif mode == "relative-symlink":
            relative = Path(os.path.relpath(source, start=destination.parent))
            destination.symlink_to(relative, target_is_directory=True)
        elif mode == "absolute-symlink":
            destination.symlink_to(source, target_is_directory=True)
        else:
            raise ValueError(f"unsupported fixture topology: {mode}")
    return repository


def run_target(
    *,
    topology: str,
    package: Path,
    entry_point: str,
    arguments: list[str],
    runtime_root: Path,
    canonical_repository: Path,
    task_output: Path,
) -> dict[str, Any]:
    """Execute the real target entry point and validate its declared authorities."""

    lexical_package = package.expanduser().absolute()
    entry = lexical_package / Path(*PurePosixPath(entry_point).parts)
    if not entry.is_file():
        raise ValueError(f"target entry point is not a file: {entry}")
    task_output.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment.update(
        {
            "CANONICAL_SKILL_REPOSITORY": str(canonical_repository),
            "CODEX_HOME": str(runtime_root),
            "TASK_OUTPUT_ROOT": str(task_output),
            "TOPOLOGY_NAME": topology,
        }
    )
    completed = subprocess.run(
        [sys.executable, str(entry), *arguments],
        cwd=lexical_package,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    parsed: Any = None
    try:
        parsed = json.loads(completed.stdout) if completed.stdout else None
    except json.JSONDecodeError:
        parsed = None
    declared = parsed.get("side_effects") if isinstance(parsed, dict) else None
    side_effects = (
        [Path(value) for value in declared]
        if isinstance(declared, list) and all(isinstance(value, str) for value in declared)
        else []
    )
    side_effects_valid = bool(side_effects) and all(
        path.is_file() and contained(path, task_output) for path in side_effects
    )
    runtime_valid = (
        isinstance(parsed, dict) and parsed.get("runtime_root") == str(runtime_root)
    )
    repository_valid = (
        isinstance(parsed, dict)
        and parsed.get("repository_root") == str(canonical_repository)
    )
    replacements = [
        (str(lexical_package), "<PACKAGE>"),
        (str(lexical_package.resolve(strict=True)), "<PACKAGE>"),
        (str(task_output), "<TASK_OUTPUT>"),
    ]
    normalized_output = (
        normalize_value(parsed, replacements) if parsed is not None else None
    )
    success = (
        completed.returncode == 0
        and completed.stderr == ""
        and runtime_valid
        and repository_valid
        and side_effects_valid
    )
    return {
        "topology": topology,
        "status": "success" if success else "failure",
        "exit_status": completed.returncode,
        "stderr": completed.stderr,
        "runtime_valid": runtime_valid,
        "repository_valid": repository_valid,
        "side_effects_valid": side_effects_valid,
        "normalized_output": normalized_output,
        "lexical_package": display(lexical_package),
        "resolved_package": display(lexical_package.resolve(strict=True)),
    }


def execute_matrix(
    *,
    canonical_repository: Path,
    source_package: Path,
    entry_point: str,
    arguments: list[str],
    runtime_root: Path,
    siblings: list[tuple[str, Path]],
    include_siblings: bool = True,
) -> dict[str, Any]:
    """Execute all four topologies in an automatically disposed root."""

    repository = explicit_directory(canonical_repository, "canonical repository")
    runtime = explicit_directory(runtime_root, "runtime root")
    source, packages = validate_layout(repository, source_package, siblings)
    entry = relative_entry_point(entry_point)
    repository_before = tree_digest(repository)
    runtime_before = tree_digest(runtime)
    temporary_path: Path | None = None
    with tempfile.TemporaryDirectory(prefix="skill-runtime-topology-") as temporary:
        fixture = Path(temporary)
        temporary_path = fixture
        topology_packages: list[tuple[str, Path]] = [
            ("canonical-direct", source),
        ]
        for mode in ("copied", "relative-symlink", "absolute-symlink"):
            fixture_repository = build_fixture_repository(
                fixture_root=fixture,
                mode=mode,
                packages=packages,
                include_siblings=include_siblings,
                target_name=source.name,
            )
            topology_packages.append((mode, fixture_repository / source.name))
        rows = [
            run_target(
                topology=name,
                package=package,
                entry_point=entry,
                arguments=arguments,
                runtime_root=runtime,
                canonical_repository=repository,
                task_output=fixture / "outputs" / name,
            )
            for name, package in topology_packages
        ]
        normalized = [row["normalized_output"] for row in rows]
        unique_outputs = len(
            {json.dumps(value, sort_keys=True, ensure_ascii=False) for value in normalized}
        )
        repository_unchanged = tree_digest(repository) == repository_before
        runtime_unchanged = tree_digest(runtime) == runtime_before
        received = {
            "successful_topologies": sum(row["status"] == "success" for row in rows),
            "unique_normalized_outputs": unique_outputs,
            "repository_unchanged": repository_unchanged,
            "runtime_unchanged": runtime_unchanged,
        }
        success_before_cleanup = (
            received["successful_topologies"] == 4
            and unique_outputs == 1
            and repository_unchanged
            and runtime_unchanged
        )
        output = {
            "status": "success" if success_before_cleanup else "failure",
            "mode": MODE,
            "condition": (
                "explicit authorities and real target behavior are equal across all deployment topologies"
            ),
            "expected": {
                "successful_topologies": 4,
                "unique_normalized_outputs": 1,
                "repository_unchanged": True,
                "runtime_unchanged": True,
                "fixture_removed": True,
            },
            "received": received,
            "topologies": rows,
        }
    fixture_removed = temporary_path is not None and not temporary_path.exists()
    output["received"]["fixture_removed"] = fixture_removed
    if not fixture_removed:
        output["status"] = "failure"
    return output


TARGET_SOURCE = '''#!/usr/bin/env python3
import json
import os
from pathlib import Path

runtime = Path(os.environ["CODEX_HOME"]).resolve(strict=True)
repository = Path(os.environ["CANONICAL_SKILL_REPOSITORY"]).resolve(strict=True)
output = Path(os.environ["TASK_OUTPUT_ROOT"]).resolve(strict=True)
package = Path(__file__).parent.absolute()
resource = (package / "resource.txt").read_text(encoding="utf-8").strip()
sibling = (package.parent / "fixture-sibling" / "resource.txt").read_text(encoding="utf-8").strip()
runtime_state = (runtime / "state.txt").read_text(encoding="utf-8").strip()
repository_state = (repository / "repository-state.txt").read_text(encoding="utf-8").strip()
marker = output / "marker.txt"
marker.write_text(f"{resource}:{sibling}:{runtime_state}:{repository_state}\\n", encoding="utf-8")
print(json.dumps({
    "package_resource": resource,
    "package_root": str(package),
    "repository_root": str(repository),
    "repository_state": repository_state,
    "runtime_root": str(runtime),
    "runtime_state": runtime_state,
    "side_effects": [str(marker)],
    "sibling_resource": sibling,
    "topology": os.environ["TOPOLOGY_NAME"],
}, sort_keys=True))
'''


REGRESSION_SOURCE = TARGET_SOURCE.replace(
    'runtime = Path(os.environ["CODEX_HOME"]).resolve(strict=True)',
    'runtime = Path(__file__).resolve().parents[1]',
).replace(
    'runtime_state = (runtime / "state.txt").read_text(encoding="utf-8").strip()',
    'runtime_state = "derived-parent"',
)


def make_repository(root: Path, source: str = TARGET_SOURCE) -> tuple[Path, Path, Path]:
    """Create canonical target, sibling, repository state, and runtime fixtures."""

    repository = root / "repository"
    target = repository / "fixture-target"
    sibling = repository / "fixture-sibling"
    target.mkdir(parents=True)
    sibling.mkdir()
    (target / "resource.txt").write_text("package-resource\n", encoding="utf-8")
    entry = target / "entry.py"
    entry.write_text(source, encoding="utf-8")
    entry.chmod(0o755)
    (sibling / "resource.txt").write_text("sibling-resource\n", encoding="utf-8")
    (repository / "repository-state.txt").write_text(
        "canonical-repository-state\n",
        encoding="utf-8",
    )
    runtime = root / "runtime"
    runtime.mkdir()
    (runtime / "state.txt").write_text("harness-runtime-state\n", encoding="utf-8")
    return repository, target, runtime


def self_test() -> dict[str, Any]:
    """Exercise the positive matrix and every selected negative boundary."""

    assertions = 0
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        repository, target, runtime = make_repository(root)
        sibling = repository / "fixture-sibling"
        inherited = resolve_runtime_root(None, {"CODEX_HOME": str(runtime)})
        assert inherited == runtime
        assertions += 1

        output = execute_matrix(
            canonical_repository=repository,
            source_package=target,
            entry_point="entry.py",
            arguments=[],
            runtime_root=inherited,
            siblings=[("fixture-sibling", sibling)],
        )
        assert output["status"] == "success", output
        assert output["received"]["successful_topologies"] == 4
        assert output["received"]["unique_normalized_outputs"] == 1
        assert output["received"]["repository_unchanged"] is True
        assert output["received"]["runtime_unchanged"] is True
        assert output["received"]["fixture_removed"] is True
        assert all(row["side_effects_valid"] for row in output["topologies"])
        assertions += 7

        for environment in ({}, {"CODEX_HOME": ""}):
            try:
                resolve_runtime_root(None, environment)
            except ValueError:
                assertions += 1
            else:
                raise AssertionError("missing runtime authority was inferred from package topology")

        missing_sibling = execute_matrix(
            canonical_repository=repository,
            source_package=target,
            entry_point="entry.py",
            arguments=[],
            runtime_root=runtime,
            siblings=[("fixture-sibling", sibling)],
            include_siblings=False,
        )
        assert missing_sibling["status"] == "failure"
        assert missing_sibling["received"]["successful_topologies"] < 4
        assert missing_sibling["received"]["fixture_removed"] is True
        assertions += 3

        regression_root = root / "regression-case"
        regression_repository, regression_target, regression_runtime = make_repository(
            regression_root,
            REGRESSION_SOURCE,
        )
        regression = execute_matrix(
            canonical_repository=regression_repository,
            source_package=regression_target,
            entry_point="entry.py",
            arguments=[],
            runtime_root=regression_runtime,
            siblings=[
                ("fixture-sibling", regression_repository / "fixture-sibling")
            ],
        )
        assert regression["status"] == "failure"
        assert regression["received"]["successful_topologies"] == 0
        assert regression["received"]["fixture_removed"] is True
        assertions += 3

        try:
            parse_sibling("bad")
        except ValueError:
            assertions += 1
        else:
            raise AssertionError("malformed sibling declaration was accepted")

        try:
            relative_entry_point("../entry.py")
        except ValueError:
            assertions += 1
        else:
            raise AssertionError("escaping entry point was accepted")

    return {"status": "passed", "assertions": assertions, "mode": MODE}


def parse_args() -> argparse.Namespace:
    """Parse target, authority, argument, and sibling declarations."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-repository", type=Path)
    parser.add_argument("--source-package", type=Path)
    parser.add_argument("--entry-point")
    parser.add_argument("--target-arg", action="append", default=[])
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--sibling-package", action="append", default=[])
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if not arguments.self_test and any(
        value is None
        for value in (
            arguments.canonical_repository,
            arguments.source_package,
            arguments.entry_point,
        )
    ):
        parser.error(
            "--canonical-repository, --source-package, and --entry-point are required"
        )
    return arguments


def main() -> int:
    """Execute one matrix with machine-readable evidence."""

    arguments = parse_args()
    try:
        if arguments.self_test:
            output = self_test()
        else:
            runtime = resolve_runtime_root(arguments.runtime_root, os.environ)
            output = execute_matrix(
                canonical_repository=arguments.canonical_repository,
                source_package=arguments.source_package,
                entry_point=arguments.entry_point,
                arguments=arguments.target_arg,
                runtime_root=runtime,
                siblings=[parse_sibling(value) for value in arguments.sibling_package],
            )
    except (OSError, RuntimeError, ValueError) as error:
        output = {
            "status": "failure",
            "mode": MODE,
            "condition": "the explicit-authority topology matrix completes",
            "expected": "valid target, authorities, and sibling declarations",
            "received": normalize_error(error),
        }
    print(json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if output["status"] in {"success", "passed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
