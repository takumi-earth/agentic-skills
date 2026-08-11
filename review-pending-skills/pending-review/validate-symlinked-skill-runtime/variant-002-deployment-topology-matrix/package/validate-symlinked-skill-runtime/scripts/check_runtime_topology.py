#!/usr/bin/env python3
"""Execute a target entry point through a disposable deployment topology matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any


MODE = "deployment-topology-matrix"


def display(path: Path) -> str:
    """Render paths beneath the user home as `~/...`."""

    absolute = path.expanduser().absolute()
    home = Path.home().resolve(strict=False)
    try:
        relative = absolute.relative_to(home)
    except ValueError:
        return str(absolute)
    return "~" if relative == Path(".") else f"~/{relative.as_posix()}"


def relative_entry_point(value: str) -> str:
    """Require a canonical package-relative entry-point path."""

    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or ".." in path.parts or not path.parts:
        raise ValueError(f"entry point must be package-relative: {value!r}")
    return value


def tree_digest(root: Path) -> str:
    """Hash exact paths, bytes, executable modes, and symlink targets."""

    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"tree root is not a real directory: {root}")
    digest = hashlib.sha256()
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
                raise ValueError(f"unsupported fixture entry: {relative}")
    for relative, mode, payload in sorted(entries):
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(mode.encode())
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return digest.hexdigest()


def normalize_value(value: Any, replacements: list[tuple[str, str]]) -> Any:
    """Normalize topology-specific paths in target output."""

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
    """Return whether one resolved path stays beneath the selected root."""

    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=True))
    except ValueError:
        return False
    return True


def build_topologies(source: Path, fixture_root: Path) -> list[tuple[str, Path]]:
    """Create copied, relative-link, and absolute-link deployments."""

    copied = fixture_root / "copied"
    shutil.copytree(source, copied, symlinks=True)
    relative_link = fixture_root / "relative-link"
    relative_target = Path(os.path.relpath(source, start=relative_link.parent))
    relative_link.symlink_to(relative_target, target_is_directory=True)
    absolute_link = fixture_root / "absolute-link"
    absolute_link.symlink_to(source, target_is_directory=True)
    return [
        ("canonical-direct", source),
        ("copied", copied),
        ("relative-symlink", relative_link),
        ("absolute-symlink", absolute_link),
    ]


def run_target(
    *,
    name: str,
    package: Path,
    entry_point: str,
    runtime_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Execute the target's real entry point and validate declared side effects."""

    lexical_package = package.expanduser().absolute()
    entry = lexical_package / Path(*PurePosixPath(entry_point).parts)
    if not entry.is_file():
        raise ValueError(f"target entry point is not a file: {entry}")
    output_root.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment.update(
        {
            "CODEX_HOME": str(runtime_root),
            "TASK_OUTPUT_ROOT": str(output_root),
            "TOPOLOGY_NAME": name,
        }
    )
    completed = subprocess.run(
        [sys.executable, str(entry)],
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
        path.is_file() and contained(path, output_root) for path in side_effects
    )
    runtime_valid = (
        isinstance(parsed, dict) and parsed.get("runtime_root") == str(runtime_root)
    )
    replacements = [
        (str(lexical_package), "<PACKAGE>"),
        (str(lexical_package.resolve(strict=True)), "<PACKAGE>"),
        (str(output_root), "<TASK_OUTPUT>"),
    ]
    normalized = normalize_value(parsed, replacements) if parsed is not None else None
    success = (
        completed.returncode == 0
        and completed.stderr == ""
        and runtime_valid
        and side_effects_valid
    )
    return {
        "topology": name,
        "status": "success" if success else "failure",
        "exit_status": completed.returncode,
        "stderr": completed.stderr,
        "runtime_valid": runtime_valid,
        "side_effects_valid": side_effects_valid,
        "normalized_output": normalized,
        "lexical_package": display(lexical_package),
        "resolved_package": display(lexical_package.resolve(strict=True)),
    }


def run_matrix(
    *,
    source_package: Path,
    entry_point: str,
    runtime_root: Path,
    fixture_root: Path,
) -> dict[str, Any]:
    """Build the matrix, execute the target, and compare observable behavior."""

    source = source_package.expanduser().resolve(strict=True)
    runtime = runtime_root.expanduser().resolve(strict=True)
    if not source.is_dir() or not runtime.is_dir():
        raise ValueError("source package and runtime root must be existing directories")
    entry = relative_entry_point(entry_point)
    fixture = fixture_root.expanduser().resolve(strict=False)
    fixture.mkdir(parents=True, exist_ok=False)
    source_before = tree_digest(source)
    runtime_before = tree_digest(runtime)
    topologies = build_topologies(source, fixture)
    rows = [
        run_target(
            name=name,
            package=package,
            entry_point=entry,
            runtime_root=runtime,
            output_root=fixture / "outputs" / name,
        )
        for name, package in topologies
    ]
    source_unchanged = tree_digest(source) == source_before
    runtime_unchanged = tree_digest(runtime) == runtime_before
    normalized = [row["normalized_output"] for row in rows]
    unique_outputs = len({json.dumps(value, sort_keys=True) for value in normalized})
    success = (
        all(row["status"] == "success" for row in rows)
        and unique_outputs == 1
        and source_unchanged
        and runtime_unchanged
    )
    return {
        "status": "success" if success else "failure",
        "mode": MODE,
        "condition": (
            "the real target entry point has equal behavior across direct, copied, and linked deployments"
        ),
        "expected": {
            "successful_topologies": 4,
            "unique_normalized_outputs": 1,
            "source_unchanged": True,
            "runtime_unchanged": True,
        },
        "received": {
            "successful_topologies": sum(row["status"] == "success" for row in rows),
            "unique_normalized_outputs": unique_outputs,
            "source_unchanged": source_unchanged,
            "runtime_unchanged": runtime_unchanged,
        },
        "topologies": rows,
    }


TARGET_SOURCE = '''#!/usr/bin/env python3
import json
import os
from pathlib import Path

runtime = Path(os.environ["CODEX_HOME"]).resolve(strict=True)
output = Path(os.environ["TASK_OUTPUT_ROOT"]).resolve(strict=True)
resource = (Path(__file__).parent / "resource.txt").read_text(encoding="utf-8").strip()
state = (runtime / "state.txt").read_text(encoding="utf-8").strip()
marker = output / "marker.txt"
marker.write_text(f"{resource}:{state}\\n", encoding="utf-8")
print(json.dumps({
    "package_root": str(Path(__file__).parent.absolute()),
    "resource": resource,
    "runtime_root": str(runtime),
    "side_effects": [str(marker)],
    "state": state,
    "topology": os.environ["TOPOLOGY_NAME"],
}, sort_keys=True))
'''


REGRESSION_SOURCE = TARGET_SOURCE.replace(
    'runtime = Path(os.environ["CODEX_HOME"]).resolve(strict=True)',
    'runtime = Path(__file__).resolve().parents[1]',
).replace(
    'state = (runtime / "state.txt").read_text(encoding="utf-8").strip()',
    'state = "derived-parent"',
)


def write_target(package: Path, source: str = TARGET_SOURCE) -> None:
    """Create a disposable package whose entry point exposes real behavior."""

    package.mkdir(parents=True)
    (package / "resource.txt").write_text("fixture-resource\n", encoding="utf-8")
    entry = package / "entry.py"
    entry.write_text(source, encoding="utf-8")
    entry.chmod(0o755)


def self_test() -> dict[str, Any]:
    """Exercise positive parity, containment, and a resolved-parent regression."""

    assertions = 0
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = root / "source"
        write_target(source)
        runtime = root / "runtime"
        runtime.mkdir()
        (runtime / "state.txt").write_text("runtime-state\n", encoding="utf-8")
        output = run_matrix(
            source_package=source,
            entry_point="entry.py",
            runtime_root=runtime,
            fixture_root=root / "matrix",
        )
        assert output["status"] == "success", output
        assert output["received"]["successful_topologies"] == 4
        assert output["received"]["unique_normalized_outputs"] == 1
        assert output["received"]["source_unchanged"] is True
        assert output["received"]["runtime_unchanged"] is True
        assert {row["topology"] for row in output["topologies"]} == {
            "canonical-direct",
            "copied",
            "relative-symlink",
            "absolute-symlink",
        }
        assert all(row["side_effects_valid"] for row in output["topologies"])
        assertions += 7

        regression = root / "regression"
        write_target(regression, REGRESSION_SOURCE)
        failed = run_matrix(
            source_package=regression,
            entry_point="entry.py",
            runtime_root=runtime,
            fixture_root=root / "regression-matrix",
        )
        assert failed["status"] == "failure"
        assert failed["received"]["successful_topologies"] < 4
        assertions += 2

        try:
            relative_entry_point("../entry.py")
        except ValueError:
            assertions += 1
        else:
            raise AssertionError("an escaping entry point was accepted")

    return {"status": "passed", "assertions": assertions, "mode": MODE}


def parse_args() -> argparse.Namespace:
    """Parse one real target and disposable matrix root."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-package", type=Path)
    parser.add_argument("--entry-point")
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--fixture-root", type=Path)
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if not arguments.self_test and any(
        value is None
        for value in (
            arguments.source_package,
            arguments.entry_point,
            arguments.runtime_root,
            arguments.fixture_root,
        )
    ):
        parser.error(
            "--source-package, --entry-point, --runtime-root, and --fixture-root are required"
        )
    return arguments


def main() -> int:
    """Execute the matrix and report process, output, and side-effect parity."""

    arguments = parse_args()
    try:
        output = (
            self_test()
            if arguments.self_test
            else run_matrix(
                source_package=arguments.source_package,
                entry_point=arguments.entry_point,
                runtime_root=arguments.runtime_root,
                fixture_root=arguments.fixture_root,
            )
        )
    except (OSError, RuntimeError, ValueError) as error:
        output = {
            "status": "failure",
            "mode": MODE,
            "condition": "the disposable real-entry-point topology matrix completes",
            "expected": "valid package, runtime, entry point, and fixture root",
            "received": str(error).replace(str(Path.home()), "~"),
        }
    print(json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if output["status"] in {"success", "passed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
