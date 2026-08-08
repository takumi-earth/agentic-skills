#!/usr/bin/env python3
"""Behavior tests for canonical Agentic Skills checkout resolution."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIRECTORY))

from resolve_agentic_skills_repo import CANONICAL_IDENTITY  # noqa: E402
from resolve_agentic_skills_repo import CANONICAL_REMOTE  # noqa: E402
from resolve_agentic_skills_repo import ResolutionError  # noqa: E402
from resolve_agentic_skills_repo import normalize_remote  # noqa: E402
from resolve_agentic_skills_repo import path_distance  # noqa: E402
from resolve_agentic_skills_repo import render_path  # noqa: E402
from resolve_agentic_skills_repo import resolve_repository  # noqa: E402


class ResolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.home.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def repository(self, relative: str, remote: str) -> Path:
        path = self.home / relative
        path.mkdir(parents=True)
        subprocess.run(
            ["git", "init", "--quiet", "--initial-branch=main"],
            cwd=path,
            check=True,
        )
        subprocess.run(
            ["git", "remote", "add", "origin", remote],
            cwd=path,
            check=True,
        )
        package = path / "auto-skill-creator"
        package.mkdir()
        (package / "SKILL.md").write_text(
            "---\nname: auto-skill-creator\ndescription: test\n---\n",
            encoding="utf-8",
        )
        return path

    def resolve(self, *candidates: Path, executing: Path | None = None) -> dict[str, object]:
        original_directory = Path.cwd()
        try:
            os.chdir(self.root)
            return resolve_repository(
                home=self.home,
                explicit_candidates=candidates,
                search_roots=[],
                max_depth=6,
                executing_path=executing,
            )
        finally:
            os.chdir(original_directory)

    def test_normalizes_https_ssh_and_scp_remotes(self) -> None:
        for remote in (
            "https://github.com/takumi-earth/agentic-skills.git",
            "ssh://git@github.com/takumi-earth/agentic-skills.git",
            "git@github.com:takumi-earth/agentic-skills.git",
        ):
            with self.subTest(remote=remote):
                self.assertEqual(normalize_remote(remote), CANONICAL_IDENTITY)

    def test_selects_checkout_closest_to_home(self) -> None:
        near = self.repository("agentic-skills", CANONICAL_REMOTE)
        far = self.repository(
            "src/tools/checkouts/agentic-skills",
            "git@github.com:takumi-earth/agentic-skills.git",
        )

        report = self.resolve(far, near)

        self.assertEqual(report["selected"]["path"], "~/agentic-skills")
        self.assertEqual(report["home"], "~")
        self.assertLess(path_distance(self.home, near), path_distance(self.home, far))

    def test_remote_identity_precedes_proximity(self) -> None:
        wrong = self.repository("wrong", "https://github.com/example/other.git")
        canonical = self.repository(
            "deep/canonical", "https://github.com/takumi-earth/agentic-skills.git"
        )

        report = self.resolve(wrong, canonical)

        self.assertEqual(report["selected"]["path"], "~/deep/canonical")
        self.assertEqual(
            report["rejected_candidates"][0]["rejection"],
            "remote_identity_mismatch",
        )

    def test_executing_checkout_breaks_equal_distance_tie(self) -> None:
        first = self.repository("one/repo", CANONICAL_REMOTE)
        second = self.repository("two/repo", CANONICAL_REMOTE)

        report = self.resolve(
            first,
            second,
            executing=second / "auto-skill-creator" / "SKILL.md",
        )

        self.assertEqual(report["selected"]["path"], "~/two/repo")
        self.assertEqual(report["scratchpad_root"], "~/two/repo/.scratchpad")

    def test_renders_home_paths_portably_and_preserves_external_paths(self) -> None:
        nested = self.home / "work" / "repo"
        external = self.root / "external"

        self.assertEqual(render_path(nested, self.home), "~/work/repo")
        self.assertEqual(render_path(self.home, self.home), "~")
        self.assertEqual(render_path(external, self.home), str(external.resolve()))

    def test_fails_when_no_canonical_checkout_exists(self) -> None:
        wrong = self.repository("wrong", "https://github.com/example/other.git")

        with self.assertRaises(ResolutionError):
            self.resolve(wrong)


if __name__ == "__main__":
    unittest.main()
