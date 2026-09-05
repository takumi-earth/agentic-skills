#!/usr/bin/env python3
"""Exercise source, module, and installed-version discovery without installation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("resolve_skills_ref.py")
REPO = next(parent for parent in SCRIPT.resolve().parents if (parent / "review-pending-skills").is_dir())


class ResolverTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="resolver-test-", dir=REPO / ".scratchpad")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()

    def source(self, installed_version: str | None = "1.2.3") -> tuple[Path, dict[str, str]]:
        source = self.repo / "vendor/skills-ref"
        package = source / "src/fixture_skills_ref"
        package.mkdir(parents=True)
        package.joinpath("__init__.py").write_text("raise RuntimeError('module execution is not discovery')\n")
        scripts = source / "scripts"
        scripts.mkdir()
        (scripts / "quick_validate.py").write_text("print('ok')\n")
        source.joinpath("pyproject.toml").write_text(
            "[project]\nname = 'fixture-skills-ref'\nversion = '1.2.3'\n"
            "dependencies = ['strictyaml>=1']\n\n"
            "[build-system]\nrequires = ['setuptools']\nbuild-backend = 'setuptools.build_meta'\n"
        )
        if installed_version is not None:
            distribution = source / f"src/fixture_skills_ref-{installed_version}.dist-info"
            distribution.mkdir()
            (distribution / "METADATA").write_text(
                f"Metadata-Version: 2.1\nName: fixture-skills-ref\nVersion: {installed_version}\n"
            )
        binary = self.repo / "bin"
        binary.mkdir()
        executable = binary / "fixture-skills-ref"
        executable.write_text("#!/bin/sh\nexit 0\n")
        executable.chmod(0o755)
        environment = os.environ.copy()
        environment["PATH"] = str(binary) + os.pathsep + environment.get("PATH", "")
        environment["PYTHONPATH"] = str(source / "src")
        return source, environment

    def invoke(
        self, source: str = "vendor/skills-ref", environment: dict[str, str] | None = None,
        module: str = "fixture_skills_ref", cli: str = "fixture-skills-ref",
    ) -> tuple[int, dict]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), "--source", source,
             "--module-name", module, "--cli-name", cli],
            capture_output=True, text=True, check=False, env=environment, timeout=10,
        )
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def test_matching_versions_and_source_do_not_execute_module(self) -> None:
        source, environment = self.source()
        code, report = self.invoke(environment=environment)
        self.assertEqual(code, 0)
        self.assertEqual(report["module"]["state"], "discoverable")
        self.assertFalse(report["module"]["import_executed"])
        self.assertEqual(report["cli"]["state"], "present")
        self.assertEqual(report["provenance"], "matches-pinned-source")
        self.assertEqual(report["version_agreement"], "matches")
        self.assertEqual(report["installed_distribution"]["version"], "1.2.3")
        self.assertFalse(report["helpers"][0]["executable"])
        self.assertEqual(report["helpers"][0]["recommended_invocation"][0], "python3")
        self.assertEqual(report["install_plan"][:5], ["python3", "-m", "pip", "install", "-e"])
        self.assertFalse(report["mutated_environment"])
        self.assertTrue(source.is_dir())

    def test_different_installed_version_is_independent_of_matching_origin(self) -> None:
        _, environment = self.source(installed_version="2.0.0")
        code, report = self.invoke(environment=environment)
        self.assertEqual(code, 0)
        self.assertEqual(report["provenance"], "matches-pinned-source")
        self.assertEqual(report["version_agreement"], "different")
        self.assertEqual(report["metadata"]["version"], "1.2.3")
        self.assertEqual(report["installed_distribution"]["version"], "2.0.0")

    def test_discoverable_module_without_distribution_has_unresolved_version(self) -> None:
        _, environment = self.source(installed_version=None)
        code, report = self.invoke(environment=environment)
        self.assertEqual(code, 0)
        self.assertEqual(report["module"]["state"], "discoverable")
        self.assertEqual(report["installed_distribution"]["state"], "missing")
        self.assertEqual(report["version_agreement"], "unresolved")

    def test_missing_components_do_not_create_an_install_plan(self) -> None:
        code, report = self.invoke(
            source="vendor/missing", module="definitely_missing_fixture_module",
            cli="definitely-missing-fixture-cli",
        )
        self.assertEqual(code, 0)
        self.assertEqual(report["source"]["state"], "missing")
        self.assertEqual(report["module"]["state"], "missing")
        self.assertEqual(report["cli"]["state"], "missing")
        self.assertIsNone(report["install_plan"])
        self.assertFalse((self.repo / "vendor").exists())

    def test_different_module_origin_does_not_become_matching_from_version(self) -> None:
        _, environment = self.source()
        other = self.root / "other"
        (other / "fixture_skills_ref").mkdir(parents=True)
        (other / "fixture_skills_ref/__init__.py").write_text("")
        environment["PYTHONPATH"] = str(other) + os.pathsep + environment["PYTHONPATH"]
        code, report = self.invoke(environment=environment)
        self.assertEqual(code, 0)
        self.assertEqual(report["provenance"], "different-origin")
        self.assertEqual(report["version_agreement"], "matches")

    def test_external_and_symlinked_sources_are_rejected(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        (self.repo / "linked-source").symlink_to(outside, target_is_directory=True)
        for source in (str(outside), "linked-source"):
            with self.subTest(source=source):
                code, report = self.invoke(source=source)
                self.assertEqual((code, report["status"]), (2, "invalid-source"))

    def test_invalid_source_metadata_does_not_emit_install_authority(self) -> None:
        source, environment = self.source()
        (source / "pyproject.toml").write_text("[project]\nname = 'fixture-skills-ref'\n")
        code, report = self.invoke(environment=environment)
        self.assertEqual(code, 0)
        self.assertEqual(report["source"]["state"], "invalid")
        self.assertTrue(report["metadata_errors"])
        self.assertIsNone(report["install_plan"])
        self.assertEqual(report["version_agreement"], "unresolved")

    def test_dotted_lookup_is_rejected_without_importing_parent(self) -> None:
        _, environment = self.source()
        code, report = self.invoke(environment=environment, module="fixture_skills_ref.child")
        self.assertEqual((code, report["status"]), (2, "invalid-input"))

    def test_home_paths_are_normalized_in_discovery_and_install_plan(self) -> None:
        _, environment = self.source()
        code, report = self.invoke(environment=environment)
        self.assertEqual(code, 0)
        self.assertTrue(report["repository"].startswith("~/"))
        self.assertTrue(report["module"]["origin"].startswith("~/"))
        self.assertTrue(report["install_plan"][-1].startswith("~/"))


if __name__ == "__main__":
    unittest.main()
