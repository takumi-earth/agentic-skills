#!/usr/bin/env python3
"""Direct tests for resolve_skills_ref.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("resolve_skills_ref.py")


def write_source(root: Path, module_name: str = "fixture_skills_ref") -> Path:
    source = root / "vendor" / "skills-ref"
    package = source / "src" / module_name
    scripts = source / "scripts"
    package.mkdir(parents=True)
    scripts.mkdir()
    (package / "__init__.py").write_text("__version__ = '1.2.3'\n", encoding="utf-8")
    (scripts / "quick_validate.py").write_text("print('ok')\n", encoding="utf-8")
    (source / "pyproject.toml").write_text(
        "[build-system]\n"
        "requires = ['setuptools']\n"
        "build-backend = 'setuptools.build_meta'\n\n"
        "[project]\n"
        "name = 'fixture-skills-ref'\n"
        "version = '1.2.3'\n"
        "dependencies = ['strictyaml>=1']\n",
        encoding="utf-8",
    )
    return source


class ResolverTest(unittest.TestCase):
    def run_resolver(self, repo: Path, source: str, cli: str, module: str, env: dict[str, str] | None = None) -> tuple[int, dict[str, object]]:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo",
                str(repo),
                "--source",
                source,
                "--cli-name",
                cli,
                "--module-name",
                module,
                "--json",
            ],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        return result.returncode, json.loads(result.stdout)

    def test_reports_matching_source_cli_module_and_helper_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            source = write_source(repo)
            bin_dir = repo / "bin"
            bin_dir.mkdir()
            cli = bin_dir / "fixture-skills-ref"
            cli.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            cli.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
            env["PYTHONPATH"] = str(source / "src")
            code, output = self.run_resolver(repo, "vendor/skills-ref", "fixture-skills-ref", "fixture_skills_ref", env)
        self.assertEqual(code, 0)
        self.assertEqual(output["cli"]["state"], "present")
        self.assertEqual(output["module"]["state"], "present")
        self.assertEqual(output["provenance"], "matches-pinned-source")
        self.assertFalse(output["helpers"][0]["executable"])
        self.assertFalse(output["mutated_environment"])

    def test_reports_missing_components_without_installing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            code, output = self.run_resolver(repo, "vendor/missing", "definitely-missing-cli", "definitely_missing_module")
        self.assertEqual(code, 0)
        self.assertEqual(output["source"]["state"], "missing")
        self.assertEqual(output["cli"]["state"], "missing")
        self.assertEqual(output["module"]["state"], "missing")
        self.assertIsNone(output["install_plan"])

    def test_detects_different_module_origin(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            write_source(repo)
            other = root / "other"
            package = other / "fixture_skills_ref"
            package.mkdir(parents=True)
            (package / "__init__.py").write_text("", encoding="utf-8")
            env = os.environ.copy()
            env["PYTHONPATH"] = str(other)
            code, output = self.run_resolver(repo, "vendor/skills-ref", "definitely-missing-cli", "fixture_skills_ref", env)
        self.assertEqual(code, 0)
        self.assertEqual(output["provenance"], "different-origin")

    def test_rejects_source_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            outside = root / "outside"
            outside.mkdir()
            code, output = self.run_resolver(repo, str(outside), "missing", "missing_module")
        self.assertEqual(code, 2)
        self.assertEqual(output["status"], "invalid-source")


if __name__ == "__main__":
    unittest.main()
