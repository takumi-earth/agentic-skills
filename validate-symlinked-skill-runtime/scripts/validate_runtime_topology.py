#!/usr/bin/env python3
"""Validate a real stateful entry point across disposable deployment topologies."""

from __future__ import annotations

import argparse
import errno
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


def tree_state(
    root: Path, excluded: tuple[Path, ...] = ()
) -> dict[str, dict[str, Any]]:
    """Observe files, empty directories, modes, and links without following links."""

    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"tree root is not a real directory: {root}")
    entries: dict[str, dict[str, Any]] = {}

    def observe(path: Path) -> None:
        metadata = path.lstat()
        item: dict[str, Any] = {"mode": stat.S_IMODE(metadata.st_mode)}
        if stat.S_ISLNK(metadata.st_mode):
            item.update(kind="symlink", target=os.readlink(path))
        elif stat.S_ISREG(metadata.st_mode):
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            item.update(kind="file", sha256=digest.hexdigest())
        elif stat.S_ISDIR(metadata.st_mode):
            item["kind"] = "directory"
        else:
            raise ValueError(f"unsupported tree entry: {display(path)}")
        entries[path.relative_to(root).as_posix()] = item

    def raise_walk_error(error: OSError) -> None:
        raise error

    observe(root)
    for directory, names, filenames in os.walk(
        root, followlinks=False, onerror=raise_walk_error
    ):
        parent = Path(directory)
        names[:] = [
            name for name in names
            if not any((parent / name).is_relative_to(skip) for skip in excluded)
        ]
        for name in [*names, *filenames]:
            path = parent / name
            if not any(path.is_relative_to(skip) for skip in excluded):
                observe(path)
    return dict(sorted(entries.items()))


def tree_changes(
    before: dict[str, Any], after: dict[str, Any]
) -> dict[str, list[str]]:
    return {
        "added": sorted(after.keys() - before.keys()),
        "removed": sorted(before.keys() - after.keys()),
        "changed": sorted(
            key for key in before.keys() & after.keys() if before[key] != after[key]
        ),
    }


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
    """Normalize whole path values and descendants, preserving all object fields."""

    if isinstance(value, str):
        for original, replacement in sorted(replacements, key=lambda pair: -len(pair[0])):
            for spelling in {original, display(Path(original))}:
                if value == spelling or value.startswith(spelling + "/"):
                    return replacement + value[len(spelling):]
        return value
    if isinstance(value, list):
        return [normalize_value(item, replacements) for item in value]
    if isinstance(value, dict):
        return {
            str(key): normalize_value(item, replacements)
            for key, item in value.items()
        }
    return value


def render_value(value: Any) -> Any:
    """Normalize home paths only when rendering, after semantic comparisons."""

    if isinstance(value, str):
        return re.sub(
            re.escape(str(Path.home())) + r"(?=/|$|[\s'\"),;:])", "~", value
        )
    if isinstance(value, list):
        return [render_value(item) for item in value]
    if isinstance(value, dict):
        return {render_value(str(key)): render_value(item) for key, item in value.items()}
    return value


def observed_authority(value: Any, expected: Path) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = Path(value).expanduser()
    return path.is_absolute() and path.resolve(strict=True) == expected


def inspect_artifacts(
    declared: Any, output_root: Path, initial_state: dict[str, Any]
) -> tuple[bool, dict[str, Any], list[str]]:
    """Compare declarations with actual output, allowing empty read-only results."""

    observed = tree_state(output_root)
    if not isinstance(declared, list) or not all(isinstance(value, str) for value in declared):
        return False, observed, []
    roots: dict[Path, bool] = {}
    for value in declared:
        path = Path(value).expanduser()
        if (
            not path.is_absolute()
            or ".." in path.parts
            or not path.is_relative_to(output_root)
            or not contained(path, output_root)
            or not (path.exists() or path.is_symlink())
            or path in roots
        ):
            return False, observed, []
        roots[path] = stat.S_ISDIR(path.lstat().st_mode)
    unreported = []
    for relative, state in observed.items():
        if relative == "." and state == initial_state["."]:
            continue
        path = output_root / relative
        covered = any(
            path == declared_root
            or (directory and path.is_relative_to(declared_root))
            or (state["kind"] == "directory" and declared_root.is_relative_to(path))
            for declared_root, directory in roots.items()
        )
        if not covered or not contained(path, output_root):
            unreported.append(relative)
    return not unreported, observed, unreported


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
    fixture_root: Path,
) -> dict[str, Any]:
    """Execute the real target entry point and validate its declared authorities."""

    lexical_package = package.expanduser().absolute()
    entry = lexical_package / Path(*PurePosixPath(entry_point).parts)
    if not entry.is_file():
        raise ValueError(f"target entry point is not a file: {entry}")
    task_output.mkdir(parents=True, exist_ok=False)
    initial_output = tree_state(task_output)
    fixture_before = tree_state(fixture_root, (task_output,))
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
    side_effects_valid, artifact_state, unreported = inspect_artifacts(
        declared, task_output, initial_output
    )
    fixture_delta = tree_changes(fixture_before, tree_state(fixture_root, (task_output,)))
    fixture_valid = not any(fixture_delta.values())
    runtime_valid = (
        isinstance(parsed, dict)
        and observed_authority(parsed.get("runtime_root"), runtime_root)
    )
    repository_valid = (
        isinstance(parsed, dict)
        and observed_authority(parsed.get("repository_root"), canonical_repository)
    )
    replacements = [
        (str(lexical_package), "<PACKAGE>"),
        (str(lexical_package.resolve(strict=True)), "<PACKAGE>"),
        (str(task_output), "<TASK_OUTPUT>"),
    ]
    comparable = parsed
    if isinstance(parsed, dict):
        # Only this reserved top-level field is metadata; nested fields are results.
        comparable = {key: value for key, value in parsed.items() if key != "topology"}
        if runtime_valid:
            comparable["runtime_root"] = str(runtime_root)
        if repository_valid:
            comparable["repository_root"] = str(canonical_repository)
    normalized_output = normalize_value(comparable, replacements)
    success = (
        completed.returncode == 0
        and completed.stderr == ""
        and runtime_valid
        and repository_valid
        and side_effects_valid
        and fixture_valid
    )
    return {
        "topology": topology,
        "status": "success" if success else "failure",
        "exit_status": completed.returncode,
        "stderr": completed.stderr,
        "runtime_valid": runtime_valid,
        "repository_valid": repository_valid,
        "side_effects_valid": side_effects_valid,
        "unreported_output_paths": unreported,
        "artifact_state": normalize_value(artifact_state, replacements),
        "fixture_changes_outside_task_output": fixture_delta,
        "fixture_writes_valid": fixture_valid,
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
    scratch_root: Path | None = None,
) -> dict[str, Any]:
    """Execute all four topologies in an automatically disposed root."""

    repository = explicit_directory(canonical_repository, "canonical repository")
    runtime = explicit_directory(runtime_root, "runtime root")
    source, packages = validate_layout(repository, source_package, siblings)
    entry = relative_entry_point(entry_point)
    repository_before = tree_state(repository)
    runtime_before = tree_state(runtime)
    scratch = (
        explicit_directory(scratch_root, "scratch root")
        if scratch_root is not None else (repository / ".scratchpad").resolve(strict=False)
    )
    if any(scratch.is_relative_to(package) for package in packages.values()):
        raise ValueError("scratch root must be outside the target and sibling packages")
    scratch_created = not scratch.exists()
    scratch.mkdir(exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="skill-runtime-topology-", dir=scratch) as temporary:
            fixture = Path(temporary)
            temporary_path = fixture
            topology_packages = [("canonical-direct", source)]
            for mode in ("copied", "relative-symlink", "absolute-symlink"):
                fixture_repository = build_fixture_repository(
                    fixture_root=fixture,
                    mode=mode,
                    packages=packages,
                    include_siblings=include_siblings,
                    target_name=source.name,
                )
                topology_packages.append((mode, fixture_repository / source.name))
            protected_repository = tree_state(repository, (fixture,))
            protected_runtime = tree_state(runtime, (fixture,))
            rows = []
            for name, package in topology_packages:
                row = run_target(
                    topology=name,
                    package=package,
                    entry_point=entry,
                    arguments=arguments,
                    runtime_root=runtime,
                    canonical_repository=repository,
                    task_output=fixture / "outputs" / name,
                    fixture_root=fixture,
                )
                row["repository_unchanged"] = tree_state(repository, (fixture,)) == protected_repository
                row["runtime_unchanged"] = tree_state(runtime, (fixture,)) == protected_runtime
                state_valid = row["repository_unchanged"] and row["runtime_unchanged"]
                if not state_valid:
                    row["status"] = "failure"
                rows.append(row)
                if not state_valid or not row["fixture_writes_valid"]:
                    break
    finally:
        if scratch_created:
            # Remove only our empty parent; retain unexpected target output as evidence.
            try:
                scratch.rmdir()
            except OSError as error:
                if error.errno not in {errno.ENOTEMPTY, errno.EEXIST}:
                    raise

    fixture_removed = temporary_path is not None and not temporary_path.exists()
    unique_outputs = len({json.dumps(row["normalized_output"], sort_keys=True) for row in rows})
    unique_artifacts = len({json.dumps(row["artifact_state"], sort_keys=True) for row in rows})
    received = {
        "successful_topologies": sum(row["status"] == "success" for row in rows),
        "unique_normalized_outputs": unique_outputs,
        "unique_artifact_states": unique_artifacts,
        "repository_unchanged": tree_state(repository) == repository_before,
        "runtime_unchanged": tree_state(runtime) == runtime_before,
        "fixture_removed": fixture_removed,
    }
    expected = {
        "successful_topologies": 4,
        "unique_normalized_outputs": 1,
        "unique_artifact_states": 1,
        "repository_unchanged": True,
        "runtime_unchanged": True,
        "fixture_removed": True,
    }
    return {
        "status": "success" if received == expected else "failure",
        "mode": MODE,
        "condition": "explicit authorities, reported results, and observed output artifacts have deployment parity",
        "expected": expected,
        "received": received,
        "topologies": rows,
        "not_run_topologies": [name for name, _ in topology_packages[len(rows):]],
        "observation_scope": {
            "protected_roots": [display(repository), display(runtime)],
            "controlled_fixture_changes_checked": True,
            "external_writes": "not_observed",
            "transient_reverted_changes": "not_observed",
            "preventive_sandbox": False,
        },
    }


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


def self_test(scratch_root: Path) -> dict[str, Any]:
    """Exercise the positive matrix and every selected negative boundary."""

    assertions = 0
    scratch = explicit_directory(scratch_root, "self-test scratch root")
    with tempfile.TemporaryDirectory(prefix="runtime-self-test-", dir=scratch) as temporary:
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
    parser.add_argument("--scratch-root", type=Path)
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if arguments.self_test and arguments.scratch_root is None:
        parser.error("--self-test requires --scratch-root under the canonical repository's .scratchpad")
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
            output = self_test(arguments.scratch_root)
        else:
            runtime = resolve_runtime_root(arguments.runtime_root, os.environ)
            output = execute_matrix(
                canonical_repository=arguments.canonical_repository,
                source_package=arguments.source_package,
                entry_point=arguments.entry_point,
                arguments=arguments.target_arg,
                runtime_root=runtime,
                siblings=[parse_sibling(value) for value in arguments.sibling_package],
                scratch_root=arguments.scratch_root,
            )
    except (OSError, RuntimeError, ValueError) as error:
        output = {
            "status": "failure",
            "mode": MODE,
            "condition": "the explicit-authority topology matrix completes",
            "expected": "valid target, authorities, and sibling declarations",
            "received": normalize_error(error),
        }
    print(json.dumps(render_value(output), indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if output["status"] in {"success", "passed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
