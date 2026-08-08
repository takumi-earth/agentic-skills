#!/usr/bin/env python3
"""Check that harness runtime authority is independent of package topology."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile


MODE = "explicit-runtime-root"
HOME = Path.home().resolve()


def display(path: Path) -> str:
    absolute = path.expanduser().absolute()
    try:
        relative = absolute.relative_to(HOME)
    except ValueError:
        return str(absolute)
    return "~" if relative == Path(".") else f"~/{relative.as_posix()}"


def inspect(package_paths: list[Path], runtime_root: Path) -> dict[str, object]:
    lexical = [path.expanduser().absolute() for path in package_paths]
    resolved = [path.resolve(strict=True) for path in lexical]
    runtime = runtime_root.expanduser().resolve(strict=False)
    return {
        "status": "success",
        "mode": MODE,
        "condition": "all deployment topologies use one explicit harness runtime root",
        "expected": {"runtime_root_count": 1},
        "received": {"runtime_root_count": 1},
        "runtime_root": display(runtime),
        "packages": [
            {"lexical": display(item), "resolved": display(target)}
            for item, target in zip(lexical, resolved, strict=True)
        ],
    }


def self_test() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        canonical = root / "canonical"
        canonical.mkdir()
        (canonical / "entry.py").write_text("pass\n", encoding="utf-8")
        copied = root / "copied"
        shutil.copytree(canonical, copied)
        linked = root / "linked"
        linked.symlink_to(canonical, target_is_directory=True)
        runtime = root / "runtime"
        output = inspect([canonical, copied, linked], runtime)
        assert output["runtime_root"] == str(runtime)
        assert len(output["packages"]) == 3
        assert output["packages"][0]["resolved"] != output["packages"][1]["resolved"]
        assert output["packages"][0]["resolved"] == output["packages"][2]["resolved"]
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
    print(json.dumps(inspect(arguments.package_path, runtime), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
