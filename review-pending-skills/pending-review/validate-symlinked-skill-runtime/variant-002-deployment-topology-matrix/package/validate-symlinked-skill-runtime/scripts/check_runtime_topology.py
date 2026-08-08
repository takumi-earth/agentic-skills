#!/usr/bin/env python3
"""Exercise copied, symlinked, and canonical-direct deployment parity."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile


MODE = "deployment-topology-matrix"
HOME = Path.home().resolve()


def display(path: Path) -> str:
    absolute = path.expanduser().absolute()
    try:
        relative = absolute.relative_to(HOME)
    except ValueError:
        return str(absolute)
    return "~" if relative == Path(".") else f"~/{relative.as_posix()}"


def inspect(package_paths: list[Path], runtime_root: Path) -> dict[str, object]:
    runtime = runtime_root.expanduser().resolve(strict=False)
    rows = []
    for package in package_paths:
        lexical = package.expanduser().absolute()
        rows.append({
            "lexical_package": display(lexical),
            "resolved_package": display(lexical.resolve(strict=True)),
            "runtime_root": display(runtime),
        })
    runtime_values = {row["runtime_root"] for row in rows}
    status = "success" if len(runtime_values) == 1 else "failure"
    return {
        "status": status,
        "mode": MODE,
        "condition": "runtime root is invariant across package topologies",
        "expected": {"unique_runtime_roots": 1},
        "received": {"unique_runtime_roots": len(runtime_values)},
        "topologies": rows,
    }


def self_test() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        canonical = root / "canonical"
        canonical.mkdir()
        (canonical / "entry.py").write_text("pass\n", encoding="utf-8")
        copied = root / "copied"
        shutil.copytree(canonical, copied)
        relative_link = root / "relative-link"
        relative_link.symlink_to(Path("canonical"), target_is_directory=True)
        absolute_link = root / "absolute-link"
        absolute_link.symlink_to(canonical, target_is_directory=True)
        output = inspect([canonical, copied, relative_link, absolute_link], root / "runtime")
        assert output["status"] == "success"
        assert output["received"]["unique_runtime_roots"] == 1
        assert len(output["topologies"]) == 4
        assert len({row["lexical_package"] for row in output["topologies"]}) == 4
    return {"status": "passed", "assertions": 4, "mode": MODE}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-path", action="append", type=Path, default=[])
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if not arguments.self_test and not arguments.package_path:
        parser.error("at least one --package-path is required")
    return arguments


def main() -> int:
    arguments = parse_args()
    if arguments.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return 0
    runtime = arguments.runtime_root or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    output = inspect(arguments.package_path, runtime)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
