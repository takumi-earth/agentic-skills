#!/usr/bin/env python3
"""Behavior tests for the selected skill filesystem scope guard."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIRECTORY))

from skill_change_guard import GuardError  # noqa: E402
from skill_change_guard import check_unchanged  # noqa: E402
from skill_change_guard import create_snapshot  # noqa: E402
from skill_change_guard import load_manifest  # noqa: E402
from skill_change_guard import normalize_serialized  # noqa: E402
from skill_change_guard import scan_package  # noqa: E402
from skill_change_guard import verify_snapshot  # noqa: E402


REPOSITORY_ROOT = SCRIPT_DIRECTORY.parents[1]


class SkillChangeGuardTests(unittest.TestCase):
    """Exercise both polarities of target, drift, and allowlist behavior."""

    def setUp(self) -> None:
        """Create an isolated user-skill root for one test."""

        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.skills = self.root / "skills"
        self.skills.mkdir()
        self.snapshot = self.skills / ".scratchpad" / "guard-tests" / "scope.json"

    def tearDown(self) -> None:
        """Remove the isolated test tree."""

        self.temporary.cleanup()

    def write(self, relative: str, body: str = "body\n") -> Path:
        """Write one test file beneath the temporary root."""

        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def create_existing_skill(self, name: str = "sample-skill") -> Path:
        """Create one minimal existing skill package."""

        self.write(f"skills/{name}/SKILL.md", "---\nname: sample\n---\n")
        return self.skills / name

    def test_allows_allowlisted_existing_file_modification(self) -> None:
        """An exact allowlisted file modification passes verification."""

        package = self.create_existing_skill()
        create_snapshot(self.skills, [package.name], [], self.snapshot)
        (package / "SKILL.md").write_text("changed\n", encoding="utf-8")

        verified, report = verify_snapshot(
            self.snapshot, ["sample-skill/SKILL.md"]
        )

        self.assertTrue(verified)
        self.assertEqual(report["unexpected"], [])
        self.assertEqual(
            report["changed"]["modified"], ["sample-skill/SKILL.md"]
        )

    def test_rejects_unexpected_added_file(self) -> None:
        """A non-allowlisted addition fails verification."""

        package = self.create_existing_skill()
        create_snapshot(self.skills, [package.name], [], self.snapshot)
        (package / "README.md").write_text("unexpected\n", encoding="utf-8")

        verified, report = verify_snapshot(self.snapshot, [])

        self.assertFalse(verified)
        self.assertIn("sample-skill/README.md", report["unexpected"])

    def test_rejects_unexpected_deletion(self) -> None:
        """A non-allowlisted deletion fails verification."""

        package = self.create_existing_skill()
        create_snapshot(self.skills, [package.name], [], self.snapshot)
        (package / "SKILL.md").unlink()

        verified, report = verify_snapshot(self.snapshot, [])

        self.assertFalse(verified)
        self.assertIn("sample-skill/SKILL.md", report["unexpected"])

    def test_allows_exact_new_package_outputs(self) -> None:
        """A new package passes when every created file is allowlisted."""

        create_snapshot(self.skills, [], ["new-skill"], self.snapshot)
        self.write("skills/new-skill/SKILL.md")
        self.write("skills/new-skill/agents/openai.yaml")

        verified, report = verify_snapshot(
            self.snapshot,
            ["new-skill/SKILL.md", "new-skill/agents/openai.yaml"],
        )

        self.assertTrue(verified)
        self.assertEqual(report["unexpected"], [])

    def test_rejects_expected_new_package_that_exists(self) -> None:
        """Snapshot creation rejects a pre-existing new target."""

        self.create_existing_skill("new-skill")

        with self.assertRaises(GuardError):
            create_snapshot(self.skills, [], ["new-skill"], self.snapshot)

    def test_rejects_missing_existing_package(self) -> None:
        """Snapshot creation rejects an absent existing target."""

        with self.assertRaises(GuardError):
            create_snapshot(self.skills, ["missing-skill"], [], self.snapshot)

    def test_rejects_unsafe_skill_names(self) -> None:
        """System, traversal, nested, and noncanonical targets are rejected."""

        for name in (".system", "../escape", "nested/skill", "Uppercase"):
            with self.subTest(name=name), self.assertRaises(GuardError):
                create_snapshot(self.skills, [], [name], self.snapshot)

    def test_rejects_escaping_symlink(self) -> None:
        """A package symlink may not resolve outside its package."""

        package = self.create_existing_skill()
        outside = self.write("outside.txt")
        os.symlink(outside, package / "escape")

        with self.assertRaises(GuardError):
            scan_package(package)

    def test_manifest_order_is_deterministic(self) -> None:
        """Targets and entries are sorted regardless of argument or creation order."""

        self.write("skills/z-skill/z.txt")
        self.write("skills/z-skill/a.txt")
        self.write("skills/a-skill/SKILL.md")

        create_snapshot(
            self.skills,
            ["z-skill", "a-skill", "z-skill"],
            [],
            self.snapshot,
        )
        manifest = json.loads(self.snapshot.read_text(encoding="utf-8"))

        self.assertEqual(
            [target["name"] for target in manifest["targets"]],
            ["a-skill", "z-skill"],
        )
        z_entries = manifest["targets"][1]["entries"]
        self.assertEqual(
            [entry["path"] for entry in z_entries], ["a.txt", "z.txt"]
        )

    def test_persisted_skills_root_uses_home_relative_serialization(self) -> None:
        """A manifest beneath the home directory never stores its expanded prefix."""

        with tempfile.TemporaryDirectory(
            dir=REPOSITORY_ROOT / ".scratchpad"
        ) as temporary:
            root = Path(temporary)
            skills = root / "skills"
            package = skills / "sample-skill"
            package.mkdir(parents=True)
            (package / "SKILL.md").write_text("skill\n", encoding="utf-8")
            snapshot = skills / ".scratchpad" / "guard" / "scope.json"

            manifest = create_snapshot(skills, [package.name], [], snapshot)
            persisted = json.loads(snapshot.read_text(encoding="utf-8"))
            loaded = load_manifest(snapshot)

            self.assertTrue(manifest["skills_root"].startswith("~/"))
            self.assertEqual(persisted["skills_root"], manifest["skills_root"])
            self.assertEqual(loaded["skills_root"], manifest["skills_root"])
            unchanged, report = check_unchanged(snapshot)
            self.assertTrue(unchanged)
            self.assertEqual(report["status"], "unchanged")

    def test_nested_machine_values_normalize_every_home_occurrence(self) -> None:
        """Diagnostics normalize home paths recursively without changing field names."""

        expanded = str(Path.home().resolve())
        value = {
            "path": f"{expanded}/agentic-skills",
            "nested": [f"before {expanded}/.codex after", {"count": 1}],
        }

        normalized = normalize_serialized(value)

        self.assertEqual(normalized["path"], "~/agentic-skills")
        self.assertEqual(normalized["nested"][0], "before ~/.codex after")
        self.assertEqual(normalized["nested"][1], {"count": 1})

    def test_detects_preapplication_baseline_drift(self) -> None:
        """The unchanged phase detects target edits after the snapshot."""

        package = self.create_existing_skill()
        create_snapshot(self.skills, [package.name], [], self.snapshot)
        (package / "SKILL.md").write_text("drift\n", encoding="utf-8")

        unchanged, report = check_unchanged(self.snapshot)

        self.assertFalse(unchanged)
        self.assertEqual(report["status"], "changed")

    def test_ignores_unrelated_dirty_sibling_skill(self) -> None:
        """A sibling package outside the target ledger does not cause drift."""

        target = self.create_existing_skill("target-skill")
        sibling = self.create_existing_skill("sibling-skill")
        create_snapshot(self.skills, [target.name], [], self.snapshot)
        (sibling / "SKILL.md").write_text("dirty sibling\n", encoding="utf-8")

        unchanged, report = check_unchanged(self.snapshot)

        self.assertTrue(unchanged)
        self.assertEqual(report["changes"], [])

    def test_rejects_snapshot_outside_repository_scratchpad(self) -> None:
        """The baseline manifest must not escape the repository scratchpad."""

        package = self.create_existing_skill()

        with self.assertRaises(GuardError):
            create_snapshot(
                self.skills,
                [package.name],
                [],
                self.root / "scope.json",
            )

    def test_rejects_snapshot_inside_skill_package(self) -> None:
        """The baseline manifest cannot become deployable package content."""

        package = self.create_existing_skill()

        with self.assertRaises(GuardError):
            create_snapshot(
                self.skills,
                [package.name],
                [],
                package / "scope.json",
            )


if __name__ == "__main__":
    unittest.main()
