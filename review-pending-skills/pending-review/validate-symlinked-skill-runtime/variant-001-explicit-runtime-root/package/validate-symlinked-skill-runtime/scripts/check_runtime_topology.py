#!/usr/bin/env python3
"""Run a target entry point and verify explicit runtime-root authority."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Mapping


MODE = "explicit-runtime-root"


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
    """Require a canonical package-relative entry point."""

    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or ".." in path.parts or not path.parts:
        raise ValueError(f"entry point must be package-relative: {value!r}")
    return value


def runtime_root(
    explicit: Path | None,
    environ: Mapping[str, str],
) -> Path:
    """Resolve an explicit argument or inherited `CODEX_HOME`, never a package parent."""

    if explicit is not None:
        candidate = explicit.expanduser()
    else:
        raw = environ.get("CODEX_HOME")
        if raw is None or not raw.strip():
            raise ValueError("runtime root requires --runtime-root or nonempty CODEX_HOME")
        candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        raise ValueError("runtime root must be absolute")
    resolved = candidate.resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError("runtime root must be an existing directory")
    return resolved


def contained(path: Path, root: Path) -> bool:
    """Return whether a resolved path remains beneath one root."""

    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=True))
    except ValueError:
        return False
    return True


def run_entry_point(
    *,
    package: Path,
    entry_point: str,
    authority_root: Path,
    task_output: Path,
    topology: str,
) -> dict[str, Any]:
    """Execute the target's real entry point under one package topology."""

    lexical_package = package.expanduser().absolute()
    lexical_entry = lexical_package / Path(*PurePosixPath(entry_point).parts)
    if not lexical_entry.is_file():
        raise ValueError(f"target entry point is not a file: {lexical_entry}")
    task_output.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment.update(
        {
            "CODEX_HOME": str(authority_root),
            "TASK_OUTPUT_ROOT": str(task_output),
            "TOPOLOGY_NAME": topology,
        }
    )
    completed = subprocess.run(
        [sys.executable, str(lexical_entry)],
        cwd=lexical_package,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    parsed: Any = None
    if completed.stdout:
        try:
            parsed = json.loads(completed.stdout)
        except json.JSONDecodeError:
            parsed = None
    side_effect = None
    if isinstance(parsed, dict) and isinstance(parsed.get("side_effect"), str):
        side_effect = Path(parsed["side_effect"])
    success = (
        completed.returncode == 0
        and completed.stderr == ""
        and isinstance(parsed, dict)
        and parsed.get("runtime_root") == str(authority_root)
        and side_effect is not None
        and side_effect.is_file()
        and contained(side_effect, task_output)
    )
    comparable = None
    if isinstance(parsed, dict):
        comparable = {
            key: value
            for key, value in parsed.items()
            if key not in {"side_effect", "topology"}
        }
    return {
        "topology": topology,
        "status": "success" if success else "failure",
        "exit_status": completed.returncode,
        "stderr": completed.stderr,
        "runtime_root": parsed.get("runtime_root") if isinstance(parsed, dict) else None,
        "comparable_output": comparable,
        "side_effect": display(side_effect) if side_effect is not None else None,
        "side_effect_contained": (
            contained(side_effect, task_output) if side_effect is not None else False
        ),
        "lexical_package": display(lexical_package),
        "resolved_package": display(lexical_package.resolve(strict=True)),
    }


def check(
    *,
    packages: list[Path],
    entry_point: str,
    authority_root: Path,
    task_output_root: Path,
) -> dict[str, Any]:
    """Require real-entry-point behavior to retain one explicit runtime root."""

    if not packages:
        raise ValueError("at least one package path is required")
    entry = relative_entry_point(entry_point)
    output_root = task_output_root.expanduser().resolve(strict=False)
    output_root.mkdir(parents=True, exist_ok=False)
    rows = [
        run_entry_point(
            package=package,
            entry_point=entry,
            authority_root=authority_root,
            task_output=output_root / f"topology-{index}",
            topology=f"topology-{index}",
        )
        for index, package in enumerate(packages)
    ]
    comparable = [row["comparable_output"] for row in rows]
    success = (
        all(row["status"] == "success" for row in rows)
        and len({json.dumps(value, sort_keys=True) for value in comparable}) == 1
    )
    return {
        "status": "success" if success else "failure",
        "mode": MODE,
        "condition": (
            "the target entry point uses one explicit runtime root across package topologies"
        ),
        "expected": {
            "runtime_root": display(authority_root),
            "successful_topologies": len(packages),
            "unique_outputs": 1,
        },
        "received": {
            "successful_topologies": sum(row["status"] == "success" for row in rows),
            "unique_outputs": len(
                {json.dumps(value, sort_keys=True) for value in comparable}
            ),
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
    "resource": resource,
    "runtime_root": str(runtime),
    "side_effect": str(marker),
    "state": state,
    "topology": os.environ["TOPOLOGY_NAME"],
}, sort_keys=True))
'''


REGRESSION_SOURCE = '''#!/usr/bin/env python3
import json
import os
from pathlib import Path

runtime = Path(__file__).resolve().parents[1]
output = Path(os.environ["TASK_OUTPUT_ROOT"]).resolve(strict=True)
marker = output / "marker.txt"
marker.write_text("regression\\n", encoding="utf-8")
print(json.dumps({
    "resource": "fixture-resource",
    "runtime_root": str(runtime),
    "side_effect": str(marker),
    "state": "runtime-state",
    "topology": os.environ["TOPOLOGY_NAME"],
}, sort_keys=True))
'''


def write_target(package: Path, source: str = TARGET_SOURCE) -> None:
    """Create one disposable target package with a real executable entry point."""

    package.mkdir(parents=True)
    (package / "resource.txt").write_text("fixture-resource\n", encoding="utf-8")
    entry = package / "entry.py"
    entry.write_text(source, encoding="utf-8")
    entry.chmod(0o755)


def self_test() -> dict[str, Any]:
    """Exercise actual target behavior across direct, copied, and linked packages."""

    assertions = 0
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        canonical = root / "canonical"
        write_target(canonical)
        copied = root / "copied"
        shutil.copytree(canonical, copied)
        relative_link = root / "relative-link"
        relative_link.symlink_to(Path("canonical"), target_is_directory=True)
        absolute_link = root / "absolute-link"
        absolute_link.symlink_to(canonical, target_is_directory=True)
        authority = root / "runtime"
        authority.mkdir()
        (authority / "state.txt").write_text("runtime-state\n", encoding="utf-8")

        output = check(
            packages=[canonical, copied, relative_link, absolute_link],
            entry_point="entry.py",
            authority_root=runtime_root(authority, {}),
            task_output_root=root / "outputs",
        )
        assert output["status"] == "success", output
        assert output["received"]["successful_topologies"] == 4
        assert output["received"]["unique_outputs"] == 1
        assert all(row["side_effect_contained"] for row in output["topologies"])
        assert {row["runtime_root"] for row in output["topologies"]} == {str(authority)}
        assertions += 5

        inherited = runtime_root(None, {"CODEX_HOME": str(authority)})
        assert inherited == authority
        assertions += 1
        for environment in ({}, {"CODEX_HOME": ""}):
            try:
                runtime_root(None, environment)
            except ValueError:
                assertions += 1
            else:
                raise AssertionError("missing runtime authority was inferred from package state")

        regression = root / "regression"
        write_target(regression, REGRESSION_SOURCE)
        regression_copy = root / "regression-copy"
        shutil.copytree(regression, regression_copy)
        failed = check(
            packages=[regression, regression_copy],
            entry_point="entry.py",
            authority_root=authority,
            task_output_root=root / "regression-outputs",
        )
        assert failed["status"] == "failure"
        assert failed["received"]["successful_topologies"] == 0
        assertions += 2

        try:
            relative_entry_point("../entry.py")
        except ValueError:
            assertions += 1
        else:
            raise AssertionError("escaping entry point was accepted")

    return {"status": "passed", "assertions": assertions, "mode": MODE}


def parse_args() -> argparse.Namespace:
    """Parse the target topology and explicit runtime authority."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-path", action="append", type=Path, default=[])
    parser.add_argument("--entry-point")
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--task-output-root", type=Path)
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if not arguments.self_test:
        if not arguments.package_path:
            parser.error("at least one --package-path is required")
        if arguments.entry_point is None or arguments.task_output_root is None:
            parser.error("--entry-point and --task-output-root are required")
    return arguments


def main() -> int:
    """Execute the real target and report exact parity evidence."""

    arguments = parse_args()
    try:
        if arguments.self_test:
            output = self_test()
        else:
            authority = runtime_root(arguments.runtime_root, os.environ)
            output = check(
                packages=arguments.package_path,
                entry_point=arguments.entry_point,
                authority_root=authority,
                task_output_root=arguments.task_output_root,
            )
    except (OSError, RuntimeError, ValueError) as error:
        output = {
            "status": "failure",
            "mode": MODE,
            "condition": "the target entry point uses explicit runtime authority",
            "expected": "valid package paths, entry point, runtime root, and task output",
            "received": str(error).replace(str(Path.home()), "~"),
        }
    print(json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if output["status"] in {"success", "passed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
