#!/usr/bin/env python3
"""Behavior tests for relative Agent Skills harness reconciliation."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import stat
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
SKILL_DIRECTORY = SCRIPT_DIRECTORY.parent
sys.path.insert(0, str(SCRIPT_DIRECTORY))

import link_agentic_skills as linker  # noqa: E402


class LinkAgenticSkillsTests(unittest.TestCase):
    """Exercise discovery, configuration, ownership, and CLI behavior."""

    def setUp(self) -> None:
        """Create an isolated source repository, home, and XDG root."""

        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.xdg = self.home / ".config"
        self.skills_root = self.root / "source"
        self.home.mkdir()
        self.xdg.mkdir()
        self.skills_root.mkdir()
        self.environ = {"XDG_CONFIG_HOME": str(self.xdg)}

    def tearDown(self) -> None:
        """Remove the isolated filesystem tree."""

        self.temporary.cleanup()

    def create_skill(self, name: str) -> Path:
        """Create one minimal top-level source skill."""

        package = self.skills_root / name
        package.mkdir(parents=True)
        (package / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test skill.\n---\n",
            encoding="utf-8",
        )
        return package

    def config_path(self, home_fallback: bool = False) -> Path:
        """Return one automatic config candidate."""

        if home_fallback:
            return self.home / linker.CONFIG_FILENAME
        return self.xdg / linker.CONFIG_FILENAME

    def write_config(self, body: str, home_fallback: bool = False) -> Path:
        """Write an authoritative TOML config."""

        path = self.config_path(home_fallback)
        path.write_text(body, encoding="utf-8")
        return path

    def args(
        self,
        operation: str = "sync",
        *,
        dry_run: bool = False,
        config: str | None = None,
    ) -> argparse.Namespace:
        """Build direct-call CLI arguments."""

        return argparse.Namespace(
            operation=operation,
            skills_root=str(self.skills_root),
            home=str(self.home),
            config=config,
            dry_run=dry_run,
        )

    def run_sync(
        self, *, dry_run: bool = False, config: str | None = None
    ) -> tuple[dict[str, object], int]:
        """Run sync against only the isolated environment."""

        return linker.run_sync(self.args(dry_run=dry_run, config=config), self.environ)

    @staticmethod
    def harness(report: dict[str, object], name: str) -> dict[str, object]:
        """Return one named harness report."""

        harnesses = report["harnesses"]
        assert isinstance(harnesses, list)
        return next(item for item in harnesses if item["name"] == name)

    def test_discovers_only_immediate_visible_skill_packages(self) -> None:
        """Hidden, nested, and non-package directories never become skills."""

        self.create_skill("alpha")
        for hidden_name in (".hidden", ".git", ".scratchpad", ".skill-specs"):
            hidden = self.skills_root / hidden_name
            hidden.mkdir()
            (hidden / "SKILL.md").write_text("hidden\n", encoding="utf-8")
        nested = self.skills_root / "examples" / "nested"
        nested.mkdir(parents=True)
        (nested / "SKILL.md").write_text("nested\n", encoding="utf-8")
        (self.skills_root / "ordinary").mkdir()
        (self.skills_root / "README.md").write_text("ignored\n", encoding="utf-8")
        (self.skills_root / "AGENTS.md").write_text("ignored\n", encoding="utf-8")

        discovered = linker.discover_skills(self.skills_root)

        self.assertEqual(list(discovered), ["alpha"])

    def test_rejects_noncanonical_deployable_directory_name(self) -> None:
        """A selected package must have a portable skill-directory name."""

        package = self.skills_root / "Bad_Name"
        package.mkdir()
        (package / "SKILL.md").write_text("body\n", encoding="utf-8")

        with self.assertRaises(linker.InputError):
            linker.discover_skills(self.skills_root)

    def test_invocation_metadata_matches_the_approved_contract(self) -> None:
        """Trigger and OpenAI metadata preserve the exact invocation boundary."""

        skill_text = (SKILL_DIRECTORY / "SKILL.md").read_text(encoding="utf-8")
        configuration_text = (
            SKILL_DIRECTORY / "references" / "configuration.md"
        ).read_text(encoding="utf-8")
        openai_text = (SKILL_DIRECTORY / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )

        self.assertIn("name: link-agentic-skills\n", skill_text)
        self.assertIn("Set up, preview, sync, route, and prune relative", skill_text)
        self.assertIn("explaining generic skill discovery", skill_text)
        self.assertIn("For a review, explanation, or preflight request", skill_text)
        self.assertIn("sole user-level distribution root for Codex", skill_text)
        self.assertIn("inspect `~/.codex/hooks.json`", skill_text)
        self.assertIn("must never rewrite or self-trust hook registrations", skill_text)
        self.assertIn("Do not add `[harness.codex]`", configuration_text)
        self.assertIn('There is no `"disable"` value', configuration_text)
        self.assertIn("Legacy cleanup is causally gated", configuration_text)
        self.assertIn('display_name: "Link Agentic Skills"', openai_text)
        self.assertIn(
            'short_description: "Sync relative links across local harnesses"',
            openai_text,
        )
        self.assertIn(
            "default_prompt: \"Use $link-agentic-skills to sync this repository's "
            'skills into my configured local harness directories."',
            openai_text,
        )
        self.assertIn("allow_implicit_invocation: true", openai_text)

    def test_default_source_root_is_the_real_containing_repository(self) -> None:
        """A symlinked package still resolves its source repository by real path."""

        expected = Path(linker.__file__).resolve().parents[2]

        self.assertEqual(linker.resolve_skills_root(None, self.home), expected)

    def test_builtin_registry_matches_the_documented_user_paths(self) -> None:
        """The initial native harness registry remains explicit and complete."""

        user = linker.resolve_user_directories(self.home, self.environ)
        registry = linker.builtin_registry(user)
        expected = {
            "agents": (None, self.home / ".agents" / "skills", "always"),
            "codex": (
                self.home / ".codex",
                self.home / ".codex" / "skills",
                "detected",
            ),
            "claude": (
                self.home / ".claude",
                self.home / ".claude" / "skills",
                "detected",
            ),
            "gemini": (
                self.home / ".gemini",
                self.home / ".gemini" / "skills",
                "detected",
            ),
            "kiro": (self.home / ".kiro", self.home / ".kiro" / "skills", "detected"),
            "copilot": (
                self.home / ".copilot",
                self.home / ".copilot" / "skills",
                "detected",
            ),
            "cursor": (
                self.home / ".cursor",
                self.home / ".cursor" / "skills",
                "detected",
            ),
            "cline": (
                self.home / ".cline",
                self.home / ".cline" / "skills",
                "detected",
            ),
            "windsurf": (
                self.home / ".codeium" / "windsurf",
                self.home / ".codeium" / "windsurf" / "skills",
                "detected",
            ),
            "opencode": (
                self.xdg / "opencode",
                self.xdg / "opencode" / "skills",
                "detected",
            ),
        }

        self.assertEqual(set(registry), set(expected))
        for name, (detect_dir, skills_dir, mode) in expected.items():
            with self.subTest(harness=name):
                self.assertEqual(registry[name].detect_dir, detect_dir)
                self.assertEqual(registry[name].skills_dir, skills_dir)
                self.assertEqual(registry[name].mode, mode)

    def test_cli_paths_may_be_relative_to_the_working_directory(self) -> None:
        """Ordinary relative CLI arguments do not require absolute path spelling."""

        self.create_skill("alpha")
        config = self.root / "routing.toml"
        config.write_text("schema_version = 1\n", encoding="utf-8")
        user = linker.resolve_user_directories(self.home, self.environ)
        with mock.patch.object(linker.Path, "cwd", return_value=self.root):
            source = linker.resolve_skills_root("source", user.home)
            location = linker.locate_config("routing.toml", user, require_explicit=True)

        self.assertEqual(source, self.skills_root)
        self.assertEqual(location.active, config)

    def test_home_defaults_to_path_home(self) -> None:
        """Omitting `--home` uses `Path.home()` for every built-in path."""

        with mock.patch.object(linker.Path, "home", return_value=self.home):
            user = linker.resolve_user_directories(None, {})
            registry = linker.builtin_registry(user)

        self.assertEqual(user.home, self.home)
        self.assertEqual(user.xdg_config_home, self.home / ".config")
        self.assertEqual(
            registry["agents"].skills_dir, self.home / ".agents" / "skills"
        )

    def test_default_sync_creates_agents_and_detected_harness_links(self) -> None:
        """No-config sync links all skills to agents and installed harnesses."""

        source = self.create_skill("alpha")
        (self.home / ".claude").mkdir()

        report, status = self.run_sync()

        self.assertEqual(status, 0)
        for root in (
            self.home / ".agents" / "skills",
            self.home / ".claude" / "skills",
        ):
            link = root / "alpha"
            self.assertTrue(link.is_symlink())
            target = os.readlink(link)
            self.assertFalse(os.path.isabs(target))
            self.assertEqual((link.parent / target).resolve(), source.resolve())
        self.assertEqual(self.harness(report, "gemini")["status"], "skipped")

    def test_default_sync_does_not_duplicate_agents_skills_in_codex(self) -> None:
        """Codex uses the shared root and leaves its deprecated root empty."""

        source = self.create_skill("alpha")
        (self.home / ".codex" / "skills").mkdir(parents=True)

        report, status = self.run_sync()

        agents_link = self.home / ".agents" / "skills" / "alpha"
        codex_link = self.home / ".codex" / "skills" / "alpha"
        self.assertEqual(status, 0)
        self.assertTrue(agents_link.is_symlink())
        self.assertEqual(agents_link.resolve(), source.resolve())
        self.assertFalse(os.path.lexists(codex_link))
        codex = self.harness(report, "codex")
        self.assertEqual(codex["selected_skills"], [])
        self.assertEqual(codex["purpose"], "legacy-cleanup")
        self.assertEqual(codex["target_status"], "active")

    def test_configured_codex_route_migrates_into_agents(self) -> None:
        """Legacy Codex selections move into the sole supported shared route."""

        alpha = self.create_skill("alpha")
        beta = self.create_skill("beta")
        (self.home / ".codex").mkdir()
        self.write_config(
            """schema_version = 1

[harness.agents]
mode = "always"
new_skills = "ignore"
skills = ["alpha"]

[harness.codex]
mode = "detected"
new_skills = "ignore"
skills = ["alpha", "beta"]
"""
        )

        report, status = self.run_sync()

        agents = self.home / ".agents" / "skills"
        codex = self.home / ".codex" / "skills"
        parsed = tomllib.loads(self.config_path().read_text(encoding="utf-8"))
        self.assertEqual(status, 0)
        self.assertEqual((agents / "alpha").resolve(), alpha.resolve())
        self.assertEqual((agents / "beta").resolve(), beta.resolve())
        self.assertFalse(os.path.lexists(codex / "alpha"))
        self.assertFalse(os.path.lexists(codex / "beta"))
        self.assertEqual(set(parsed["harness"]), {"agents"})
        self.assertEqual(parsed["harness"]["agents"]["skills"], ["alpha", "beta"])
        self.assertEqual(report["config"]["migration"]["removed_harness"], "codex")
        self.assertEqual(report["config"]["migration"]["destination_harness"], "agents")

    def test_configured_codex_route_creates_agents_when_missing(self) -> None:
        """A legacy Codex-only config becomes an equivalent shared-root policy."""

        source = self.create_skill("alpha")
        (self.home / ".codex").mkdir()
        self.write_config(
            """schema_version = 1

[harness.codex]
mode = "detected"
new_skills = "ignore"
skills = ["alpha"]
"""
        )

        report, status = self.run_sync()

        agents_link = self.home / ".agents" / "skills" / "alpha"
        codex_link = self.home / ".codex" / "skills" / "alpha"
        parsed = tomllib.loads(self.config_path().read_text(encoding="utf-8"))
        self.assertEqual(status, 0)
        self.assertEqual(agents_link.resolve(), source.resolve())
        self.assertFalse(os.path.lexists(codex_link))
        self.assertEqual(set(parsed["harness"]), {"agents"})
        self.assertEqual(parsed["harness"]["agents"]["skills"], ["alpha"])
        codex = self.harness(report, "codex")
        self.assertEqual(codex["selected_skills"], [])
        self.assertEqual(codex["purpose"], "legacy-cleanup")

    def test_codex_migration_dry_run_preserves_config_and_links(self) -> None:
        """Migration preview reports both sides without changing either one."""

        source = self.create_skill("alpha")
        path = self.write_config(
            """schema_version = 1

[harness.codex]
mode = "detected"
new_skills = "ignore"
skills = ["alpha"]
"""
        )
        codex = self.home / ".codex" / "skills"
        codex.mkdir(parents=True)
        codex_link = codex / "alpha"
        os.symlink(
            os.path.relpath(source, start=codex),
            codex_link,
            target_is_directory=True,
        )
        before = path.read_bytes()

        report, status = self.run_sync(dry_run=True)

        self.assertEqual(status, 0)
        self.assertEqual(path.read_bytes(), before)
        self.assertTrue(codex_link.is_symlink())
        self.assertFalse((self.home / ".agents").exists())
        self.assertEqual(report["config"]["write_status"], "would-update")
        self.assertEqual(
            self.harness(report, "agents")["actions"],
            [
                {
                    "action": "would-create",
                    "skill": "alpha",
                    "target": "../../../source/alpha",
                }
            ],
        )
        self.assertEqual(
            self.harness(report, "codex")["actions"],
            [{"action": "would-remove", "skill": "alpha"}],
        )

    def test_sync_prunes_legacy_codex_overlap_then_is_idempotent(self) -> None:
        """One sync removes a former duplicate link and later syncs stay converged."""

        source = self.create_skill("alpha")
        agents = self.home / ".agents" / "skills"
        codex = self.home / ".codex" / "skills"
        agents.mkdir(parents=True)
        codex.mkdir(parents=True)
        for destination in (agents / "alpha", codex / "alpha"):
            os.symlink(
                os.path.relpath(source, start=destination.parent),
                destination,
                target_is_directory=True,
            )

        preview, preview_status = self.run_sync(dry_run=True)
        first, first_status = self.run_sync()
        second, second_status = self.run_sync()

        self.assertEqual((preview_status, first_status, second_status), (0, 0, 0))
        preview_actions = self.harness(preview, "codex")["actions"]
        self.assertEqual(
            preview_actions,
            [{"action": "would-remove", "skill": "alpha"}],
        )
        self.assertTrue((agents / "alpha").is_symlink())
        self.assertFalse(os.path.lexists(codex / "alpha"))
        self.assertEqual(first["summary"]["removed"], 1)
        self.assertEqual(second["summary"]["created"], 0)
        self.assertEqual(second["summary"]["removed"], 0)

    def test_legacy_cleanup_stops_before_breaking_registered_hook(self) -> None:
        """A hook dependency blocks config and link writes until separately migrated."""

        source = self.create_skill("alpha")
        config = self.write_config(
            """schema_version = 1

[harness.codex]
mode = "detected"
new_skills = "ignore"
skills = ["alpha"]
"""
        )
        codex = self.home / ".codex" / "skills"
        codex.mkdir(parents=True)
        codex_link = codex / "alpha"
        os.symlink(
            os.path.relpath(source, start=codex),
            codex_link,
            target_is_directory=True,
        )
        hooks_path = self.home / ".codex" / "hooks.json"
        hooks_path.write_text(
            json.dumps(
                {
                    "hooks": {
                        "Stop": [
                            {
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": (
                                            "python3 ~/.codex/skills/alpha/"
                                            "scripts/stop_hook.py"
                                        ),
                                    }
                                ]
                            }
                        ]
                    }
                }
            ),
            encoding="utf-8",
        )
        before_config = config.read_bytes()

        report, status = self.run_sync()

        self.assertEqual(status, 1)
        self.assertFalse(report["applied"])
        self.assertEqual(report["config"]["write_status"], "blocked")
        self.assertEqual(config.read_bytes(), before_config)
        self.assertTrue(codex_link.is_symlink())
        self.assertFalse((self.home / ".agents").exists())
        self.assertEqual(len(report["errors"]), 1)
        error = report["errors"][0]
        self.assertEqual(error["code"], "deprecated-skill-hook-reference")
        self.assertEqual(error["skill"], "alpha")
        self.assertEqual(error["replacement_root"], "~/.agents/skills")
        self.assertEqual(error["json_path"], "$.hooks.Stop[0].hooks[0].command")

    def test_legacy_cleanup_accepts_hook_using_agents_projection(self) -> None:
        """An already-migrated hook does not prevent owned legacy-link cleanup."""

        source = self.create_skill("alpha")
        codex = self.home / ".codex" / "skills"
        codex.mkdir(parents=True)
        codex_link = codex / "alpha"
        os.symlink(
            os.path.relpath(source, start=codex),
            codex_link,
            target_is_directory=True,
        )
        hooks_path = self.home / ".codex" / "hooks.json"
        hooks_path.write_text(
            json.dumps(
                {
                    "hooks": {
                        "Stop": [
                            {
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": (
                                            "python3 ~/.agents/skills/alpha/"
                                            "scripts/stop_hook.py"
                                        ),
                                    }
                                ]
                            }
                        ]
                    }
                }
            ),
            encoding="utf-8",
        )

        report, status = self.run_sync()

        self.assertEqual(status, 0)
        self.assertTrue(report["applied"])
        self.assertEqual(report["errors"], [])
        self.assertFalse(os.path.lexists(codex_link))
        self.assertEqual(
            (self.home / ".agents" / "skills" / "alpha").resolve(),
            source.resolve(),
        )

    def test_source_edits_are_visible_through_an_unchanged_link(self) -> None:
        """A linked package updates in place without replacing its stable symlink."""

        source = self.create_skill("alpha")
        _, first_status = self.run_sync()
        link = self.home / ".agents" / "skills" / "alpha"
        original_target = os.readlink(link)
        (source / "SKILL.md").write_text(
            "---\nname: alpha\ndescription: Updated skill.\n---\n",
            encoding="utf-8",
        )

        report, second_status = self.run_sync()

        self.assertEqual((first_status, second_status), (0, 0))
        self.assertEqual(os.readlink(link), original_target)
        self.assertIn("Updated skill.", (link / "SKILL.md").read_text(encoding="utf-8"))
        actions = self.harness(report, "agents")["actions"]
        self.assertEqual(actions[0]["action"], "unchanged")

    def test_link_target_is_relative_to_the_physical_destination_directory(
        self,
    ) -> None:
        """A symlinked harness root still gets a link valid from its real directory."""

        source = self.create_skill("alpha")
        physical = self.home / "shared" / "skills"
        physical.mkdir(parents=True)
        agents = self.home / ".agents"
        agents.mkdir()
        os.symlink(
            physical,
            agents / "skills",
            target_is_directory=True,
        )

        _, status = self.run_sync()

        link = physical / "alpha"
        target = os.readlink(link)
        self.assertEqual(status, 0)
        self.assertFalse(os.path.isabs(target))
        self.assertEqual((physical / target).resolve(), source.resolve())

    def test_default_sync_is_idempotent(self) -> None:
        """A correct relative link remains unchanged on a later sync."""

        self.create_skill("alpha")
        first_report, first_status = self.run_sync()
        second_report, second_status = self.run_sync()

        self.assertEqual((first_status, second_status), (0, 0))
        self.assertEqual(first_report["summary"]["created"], 1)
        actions = self.harness(second_report, "agents")["actions"]
        self.assertEqual(actions[0]["action"], "unchanged")

    def test_no_config_sync_prunes_only_its_stale_owned_link(self) -> None:
        """Removing a source package removes its broken same-repository link."""

        source = self.create_skill("alpha")
        _, initial_status = self.run_sync()
        link = self.home / ".agents" / "skills" / "alpha"
        self.assertEqual(initial_status, 0)
        self.assertTrue(link.is_symlink())
        (source / "SKILL.md").unlink()
        source.rmdir()

        report, status = self.run_sync()

        self.assertEqual(status, 0)
        self.assertFalse(os.path.lexists(link))
        self.assertEqual(report["summary"]["removed"], 1)

    def test_no_config_dry_run_is_fully_read_only(self) -> None:
        """Dry-run planning does not create the always-active agents root."""

        self.create_skill("alpha")

        report, status = self.run_sync(dry_run=True)

        self.assertEqual(status, 0)
        self.assertFalse((self.home / ".agents").exists())
        actions = self.harness(report, "agents")["actions"]
        self.assertEqual(actions[0]["action"], "would-create")

    def test_dry_run_matches_apply_plan_without_mutating_filesystem_or_config(
        self,
    ) -> None:
        """A configured preview predicts additions and removal without writes."""

        for name in ("alpha", "beta", "gamma"):
            self.create_skill(name)
        path = self.write_config(
            """schema_version = 1

[harness.agents]
mode = "always"
new_skills = "ignore"
skills = ["alpha"]
exclude_skills = []
"""
        )
        _, initial_status = self.run_sync()
        self.assertEqual(initial_status, 0)
        target = self.home / ".agents" / "skills"
        self.write_config(
            """# Preserve this during preview.
schema_version = 1

[harness.agents]
mode = "always"
new_skills = "link"
skills = ["beta"]
exclude_skills = ["alpha"]
"""
        )
        before_config = path.read_bytes()

        preview, preview_status = self.run_sync(dry_run=True)

        self.assertEqual(preview_status, 0)
        self.assertFalse(preview["applied"])
        self.assertEqual(preview["config"]["write_status"], "would-update")
        self.assertEqual(path.read_bytes(), before_config)
        self.assertTrue((target / "alpha").is_symlink())
        self.assertFalse(os.path.lexists(target / "beta"))
        self.assertFalse(os.path.lexists(target / "gamma"))
        preview_actions = {
            (action["action"], action["skill"])
            for action in self.harness(preview, "agents")["actions"]
        }
        self.assertEqual(
            preview_actions,
            {
                ("would-remove", "alpha"),
                ("would-create", "beta"),
                ("would-create", "gamma"),
            },
        )

        applied, applied_status = self.run_sync()

        self.assertEqual(applied_status, 0)
        self.assertTrue(applied["applied"])
        applied_actions = {
            (action["action"], action["skill"])
            for action in self.harness(applied, "agents")["actions"]
        }
        self.assertEqual(
            applied_actions,
            {("removed", "alpha"), ("created", "beta"), ("created", "gamma")},
        )
        self.assertFalse(os.path.lexists(target / "alpha"))
        self.assertTrue((target / "beta").is_symlink())
        self.assertTrue((target / "gamma").is_symlink())
        self.assertNotEqual(path.read_bytes(), before_config)

    def test_authoritative_config_disables_unlisted_defaults(self) -> None:
        """Config presence limits processing to its named harness sections."""

        self.create_skill("alpha")
        self.write_config(
            """schema_version = 1

[harness.claude]
mode = "detected"
new_skills = "ignore"
skills = ["alpha"]
exclude_skills = []
"""
        )

        report, status = self.run_sync()

        self.assertEqual(status, 0)
        self.assertEqual([item["name"] for item in report["harnesses"]], ["claude"])
        self.assertFalse((self.home / ".agents").exists())

    def test_configured_builtin_inherits_detection_and_skills_paths(self) -> None:
        """A known harness needs no repeated native path fields in config."""

        self.create_skill("alpha")
        (self.home / ".claude").mkdir()
        self.write_config(
            """schema_version = 1

[harness.claude]
mode = "detected"
new_skills = "ignore"
skills = ["alpha"]
"""
        )

        report, status = self.run_sync()

        self.assertEqual(status, 0)
        route = self.harness(report, "claude")
        self.assertEqual(route["detect_dir"], str(self.home / ".claude"))
        self.assertEqual(route["skills_dir"], str(self.home / ".claude" / "skills"))
        self.assertTrue((self.home / ".claude" / "skills" / "alpha").is_symlink())

    def test_auto_link_updates_config_even_when_harness_is_absent(self) -> None:
        """Per-harness desired state advances independently of installation."""

        for name in ("alpha", "beta", "gamma"):
            self.create_skill(name)
        path = self.write_config(
            """# This comment is intentionally lost when routing changes.
schema_version = 1

[harness.gemini]
mode = "detected"
new_skills = "link"
skills = ["alpha"]
exclude_skills = ["beta"]
"""
        )

        report, status = self.run_sync()
        parsed = tomllib.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(status, 0)
        self.assertEqual(self.harness(report, "gemini")["status"], "skipped")
        self.assertEqual(parsed["harness"]["gemini"]["skills"], ["alpha", "gamma"])
        self.assertEqual(parsed["harness"]["gemini"]["exclude_skills"], ["beta"])
        self.assertNotIn("intentionally lost", path.read_text(encoding="utf-8"))

    def test_ignore_policy_keeps_an_explicit_allowlist(self) -> None:
        """Ignored unlisted skills are neither linked nor added to config."""

        for name in ("alpha", "beta"):
            self.create_skill(name)
        path = self.write_config(
            """# Preserve this because no routing field changes.
schema_version = 1

[harness.agents]
mode = "always"
new_skills = "ignore"
skills = ["alpha"]
exclude_skills = []
"""
        )
        before = path.read_text(encoding="utf-8")

        report, status = self.run_sync()

        self.assertEqual(status, 0)
        self.assertTrue((self.home / ".agents" / "skills" / "alpha").is_symlink())
        self.assertFalse((self.home / ".agents" / "skills" / "beta").exists())
        self.assertEqual(path.read_text(encoding="utf-8"), before)
        self.assertFalse(report["config"]["updated"])

    def test_exclusion_wins_and_removes_an_owned_link(self) -> None:
        """Adding an exclusion removes overlap from config and installed state."""

        self.create_skill("alpha")
        self.write_config(
            """schema_version = 1

[harness.agents]
mode = "always"
new_skills = "ignore"
skills = ["alpha"]
exclude_skills = []
"""
        )
        _, initial_status = self.run_sync()
        self.assertEqual(initial_status, 0)
        link = self.home / ".agents" / "skills" / "alpha"
        self.assertTrue(link.is_symlink())
        self.write_config(
            """schema_version = 1

[harness.agents]
mode = "always"
new_skills = "link"
skills = ["alpha"]
exclude_skills = ["alpha"]
"""
        )

        _, status = self.run_sync()
        parsed = tomllib.loads(self.config_path().read_text(encoding="utf-8"))

        self.assertEqual(status, 0)
        self.assertFalse(os.path.lexists(link))
        self.assertEqual(parsed["harness"]["agents"]["skills"], [])

    def test_deselection_removes_an_owned_link(self) -> None:
        """An explicit allowlist removal prunes only the repository-owned entry."""

        self.create_skill("alpha")
        self.write_config(
            """schema_version = 1

[harness.agents]
mode = "always"
new_skills = "ignore"
skills = ["alpha"]
"""
        )
        _, initial_status = self.run_sync()
        link = self.home / ".agents" / "skills" / "alpha"
        self.assertEqual(initial_status, 0)
        self.assertTrue(link.is_symlink())
        self.write_config(
            """schema_version = 1

[harness.agents]
mode = "always"
new_skills = "ignore"
skills = []
"""
        )

        report, status = self.run_sync()

        self.assertEqual(status, 0)
        self.assertFalse(os.path.lexists(link))
        self.assertEqual(report["summary"]["removed"], 1)

    def test_stale_config_and_owned_broken_link_are_pruned(self) -> None:
        """Source removal prunes desired state and only its repository-owned link."""

        self.create_skill("alpha")
        self.write_config(
            """schema_version = 1

[harness.agents]
mode = "always"
new_skills = "ignore"
skills = ["alpha", "removed-skill"]
exclude_skills = ["removed-exclusion"]
"""
        )
        target = self.home / ".agents" / "skills"
        target.mkdir(parents=True)
        stale = target / "removed-skill"
        os.symlink(
            os.path.relpath(self.skills_root / "removed-skill", start=target),
            stale,
            target_is_directory=True,
        )

        _, status = self.run_sync()
        parsed = tomllib.loads(self.config_path().read_text(encoding="utf-8"))

        self.assertEqual(status, 0)
        self.assertFalse(os.path.lexists(stale))
        self.assertEqual(parsed["harness"]["agents"]["skills"], ["alpha"])
        self.assertEqual(parsed["harness"]["agents"]["exclude_skills"], [])

    def test_deselection_preserves_another_repository_link(self) -> None:
        """A same-named link to another source repository is outside ownership."""

        other = self.root / "other" / "alpha"
        other.mkdir(parents=True)
        self.create_skill("alpha")
        self.write_config(
            """schema_version = 1

[harness.agents]
mode = "always"
new_skills = "ignore"
skills = []
exclude_skills = ["alpha"]
"""
        )
        target = self.home / ".agents" / "skills"
        target.mkdir(parents=True)
        link = target / "alpha"
        os.symlink(os.path.relpath(other, start=target), link, target_is_directory=True)

        _, status = self.run_sync()

        self.assertEqual(status, 0)
        self.assertTrue(link.is_symlink())
        self.assertEqual((target / os.readlink(link)).resolve(), other.resolve())

    def test_conflicts_are_preserved_while_other_links_continue(self) -> None:
        """Every conflicting entry type is preserved while independent work continues."""

        for name in ("alpha", "beta", "gamma", "delta", "epsilon"):
            self.create_skill(name)
        self.write_config(
            """schema_version = 1

[harness.agents]
mode = "always"
new_skills = "ignore"
skills = ["alpha", "beta", "gamma", "delta", "epsilon"]
exclude_skills = []
"""
        )
        target = self.home / ".agents" / "skills"
        target.mkdir(parents=True)
        (target / "alpha").write_text("keep me\n", encoding="utf-8")
        other_repository = self.root / "other-repository" / "beta"
        other_repository.mkdir(parents=True)
        os.symlink(
            os.path.relpath(other_repository, start=target),
            target / "beta",
            target_is_directory=True,
        )
        os.symlink(str(self.skills_root / "gamma"), target / "gamma")
        (target / "epsilon").mkdir()

        report, status = self.run_sync()

        self.assertEqual(status, 1)
        self.assertEqual((target / "alpha").read_text(encoding="utf-8"), "keep me\n")
        self.assertEqual(
            (target / os.readlink(target / "beta")).resolve(),
            other_repository.resolve(),
        )
        self.assertTrue(os.path.isabs(os.readlink(target / "gamma")))
        self.assertTrue((target / "delta").is_symlink())
        self.assertTrue((target / "epsilon").is_dir())
        self.assertEqual(report["summary"]["conflicts"], 4)
        self.assertEqual(len(report["conflicts"]), 4)
        self.assertEqual(report["errors"], [])

    def test_one_harness_error_does_not_block_an_independent_harness(self) -> None:
        """Aggregate failure preserves progress at a separately owned destination."""

        self.create_skill("alpha")
        broken_parent = self.home / ".broken"
        broken_parent.mkdir()
        (broken_parent / "skills").write_text("not a directory\n", encoding="utf-8")
        self.write_config(
            """schema_version = 1

[harness.broken]
mode = "always"
skills_dir = "~/.broken/skills"
new_skills = "ignore"
skills = ["alpha"]

[harness.working]
mode = "always"
skills_dir = "~/.working/skills"
new_skills = "ignore"
skills = ["alpha"]
"""
        )

        report, status = self.run_sync()

        self.assertEqual(status, 1)
        self.assertEqual(self.harness(report, "broken")["status"], "error")
        self.assertEqual(self.harness(report, "working")["status"], "converged")
        self.assertTrue((self.home / ".working" / "skills" / "alpha").is_symlink())
        self.assertEqual(len(report["errors"]), 1)

    def test_equivalent_relative_link_spelling_is_unchanged(self) -> None:
        """Ownership depends on lexical resolution, not one exact target string."""

        source = self.create_skill("alpha")
        target = self.home / ".agents" / "skills"
        target.mkdir(parents=True)
        relative = os.path.relpath(source, start=target)
        os.symlink(f"./{relative}", target / "alpha", target_is_directory=True)

        report, status = self.run_sync()

        self.assertEqual(status, 0)
        actions = self.harness(report, "agents")["actions"]
        self.assertEqual(actions[0]["action"], "unchanged")

    def test_detected_custom_harness_creates_only_its_skills_directory(self) -> None:
        """A custom detected root permits creation of its configured skills child."""

        self.create_skill("alpha")
        custom_root = self.home / ".custom"
        custom_root.mkdir()
        self.write_config(
            """schema_version = 1

[harness.custom]
mode = "detected"
detect_dir = "~/.custom"
skills_dir = "~/.custom/nested/skills"
new_skills = "ignore"
skills = ["alpha"]
exclude_skills = []
"""
        )

        _, status = self.run_sync()

        self.assertEqual(status, 0)
        self.assertTrue((custom_root / "nested" / "skills" / "alpha").is_symlink())

    def test_existing_custom_skills_directory_is_detection_evidence(self) -> None:
        """An existing target activates detected mode without its marker root."""

        self.create_skill("alpha")
        target = self.home / ".custom" / "skills"
        target.mkdir(parents=True)
        self.write_config(
            """schema_version = 1

[harness.custom]
mode = "detected"
detect_dir = "~/.missing-custom-root"
skills_dir = "~/.custom/skills"
new_skills = "ignore"
skills = ["alpha"]
"""
        )

        _, status = self.run_sync()

        self.assertEqual(status, 0)
        self.assertTrue((target / "alpha").is_symlink())

    def test_custom_always_harness_creates_its_root(self) -> None:
        """Always mode explicitly authorizes creation without a detection marker."""

        self.create_skill("alpha")
        self.write_config(
            """schema_version = 1

[harness.custom]
mode = "always"
skills_dir = "~/new-client/skills"
new_skills = "ignore"
skills = ["alpha"]
exclude_skills = []
"""
        )

        _, status = self.run_sync()

        self.assertEqual(status, 0)
        self.assertTrue((self.home / "new-client" / "skills" / "alpha").is_symlink())

    def test_duplicate_destination_paths_are_invalid(self) -> None:
        """Two policy owners cannot control one normalized skills directory."""

        self.create_skill("alpha")
        path = self.write_config(
            """schema_version = 1

[harness.one]
mode = "always"
skills_dir = "~/shared/skills"
new_skills = "ignore"
skills = []

[harness.two]
mode = "always"
skills_dir = "~/shared/../shared/skills"
new_skills = "ignore"
skills = []
"""
        )

        with self.assertRaises(linker.InputError):
            self.run_sync(config=str(path))

        stdout = io.StringIO()
        stderr = io.StringIO()
        argv = [
            "sync",
            "--skills-root",
            str(self.skills_root),
            "--home",
            str(self.home),
            "--config",
            str(path),
        ]
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = linker.main(argv, self.environ)

        self.assertEqual(status, 2)
        self.assertEqual(json.loads(stdout.getvalue())["status"], "invalid-input")
        self.assertIn("share skills_dir", stderr.getvalue())

    def test_invalid_config_is_rejected_before_mutation(self) -> None:
        """Malformed, incomplete, unsafe, and mistyped config is rejected early."""

        self.create_skill("alpha")
        filesystem_root = Path(self.skills_root.anchor)
        overlapping_target = self.skills_root / "nested-target"
        invalid_documents = {
            "malformed TOML": "schema_version = [\n",
            "missing schema": '[harness.agents]\nmode = "always"\nnew_skills = "ignore"\nskills = []\n',
            "wrong schema": "schema_version = 2\n",
            "boolean schema": "schema_version = true\n",
            "unknown top-level key": "schema_version = 1\nunknown = true\n",
            "unknown harness key": """schema_version = 1
[harness.agents]
mode = "always"
new_skills = "ignore"
skills = []
unknown = true
""",
            "missing required field": """schema_version = 1
[harness.agents]
mode = "always"
skills = []
""",
            "relative skills path": """schema_version = 1
[harness.custom]
mode = "always"
skills_dir = "relative/skills"
new_skills = "ignore"
skills = []
""",
            "relative detection path": """schema_version = 1
[harness.custom]
mode = "detected"
detect_dir = "relative"
skills_dir = "~/.custom/skills"
new_skills = "ignore"
skills = []
""",
            "another user home": """schema_version = 1
[harness.custom]
mode = "always"
skills_dir = "~someone/skills"
new_skills = "ignore"
skills = []
""",
            "custom missing skills path": """schema_version = 1
[harness.custom]
mode = "always"
new_skills = "ignore"
skills = []
""",
            "detected custom missing marker": """schema_version = 1
[harness.custom]
mode = "detected"
skills_dir = "~/.custom/skills"
new_skills = "ignore"
skills = []
""",
            "invalid mode": """schema_version = 1
[harness.agents]
mode = "sometimes"
new_skills = "ignore"
skills = []
""",
            "invalid new-skill policy": """schema_version = 1
[harness.agents]
mode = "always"
new_skills = "copy"
skills = []
""",
            "mistyped skill list": """schema_version = 1
[harness.agents]
mode = "always"
new_skills = "ignore"
skills = "alpha"
""",
            "selected home destination": """schema_version = 1
[harness.custom]
mode = "always"
skills_dir = "~"
new_skills = "ignore"
skills = []
""",
            "filesystem root destination": f"""schema_version = 1
[harness.custom]
mode = "always"
skills_dir = {linker.toml_string(str(filesystem_root))}
new_skills = "ignore"
skills = []
""",
            "source-overlapping destination": f"""schema_version = 1
[harness.custom]
mode = "always"
skills_dir = {linker.toml_string(str(overlapping_target))}
new_skills = "ignore"
skills = []
""",
        }
        for label, body in invalid_documents.items():
            with self.subTest(case=label):
                self.write_config(body)
                with self.assertRaises(linker.InputError):
                    self.run_sync()
                self.assertFalse((self.home / ".agents").exists())
                self.assertFalse(overlapping_target.exists())

    def test_disable_alias_error_explains_the_supported_cleanup_policy(self) -> None:
        """An intuitive invalid value points to the exact non-adding route shape."""

        self.create_skill("alpha")
        self.write_config(
            """schema_version = 1

[harness.agents]
mode = "disable"
new_skills = "disable"
skills = []
"""
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        argv = [
            "sync",
            "--skills-root",
            str(self.skills_root),
            "--home",
            str(self.home),
        ]

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = linker.main(argv, self.environ)

        report = json.loads(stdout.getvalue())
        self.assertEqual(status, 2)
        self.assertEqual(report["status"], "invalid-input")
        self.assertIn("does not support 'disable'", stderr.getvalue())
        self.assertIn("new_skills to 'ignore'", stderr.getvalue())
        self.assertIn("skills to []", stderr.getvalue())
        self.assertFalse((self.home / ".agents").exists())

    def test_malformed_config_and_source_layout_return_structured_exit_two(
        self,
    ) -> None:
        """Invalid files reach the public CLI error contract without tracebacks."""

        cases: list[tuple[str, str]] = []
        self.write_config("schema_version = [\n")
        cases.append(("malformed config", "cannot read config"))
        for label, expected_error in cases:
            with self.subTest(case=label):
                stdout = io.StringIO()
                stderr = io.StringIO()
                argv = [
                    "sync",
                    "--skills-root",
                    str(self.skills_root),
                    "--home",
                    str(self.home),
                ]
                with (
                    contextlib.redirect_stdout(stdout),
                    contextlib.redirect_stderr(stderr),
                ):
                    status = linker.main(argv, self.environ)
                report = json.loads(stdout.getvalue())
                self.assertEqual(status, 2)
                self.assertEqual(report["status"], "invalid-input")
                self.assertIn(expected_error, stderr.getvalue())

        self.config_path().unlink()
        invalid_package = self.skills_root / "Bad_Name"
        invalid_package.mkdir()
        (invalid_package / "SKILL.md").write_text("invalid\n", encoding="utf-8")
        stdout = io.StringIO()
        stderr = io.StringIO()
        argv = [
            "sync",
            "--skills-root",
            str(self.skills_root),
            "--home",
            str(self.home),
        ]
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = linker.main(argv, self.environ)
        report = json.loads(stdout.getvalue())
        self.assertEqual(status, 2)
        self.assertEqual(report["status"], "invalid-input")
        self.assertIn("lowercase hyphen-case", stderr.getvalue())

    def test_xdg_config_wins_over_home_fallback_with_warning(self) -> None:
        """Automatic lookup selects XDG deterministically when both files exist."""

        self.create_skill("alpha")
        xdg = self.write_config("schema_version = 1\n")
        fallback = self.write_config("schema_version = 1\n", home_fallback=True)
        user = linker.resolve_user_directories(self.home, self.environ)

        location = linker.locate_config(None, user)

        self.assertEqual(location.active, xdg)
        self.assertIn(str(fallback), location.warnings[0])

        stdout = io.StringIO()
        stderr = io.StringIO()
        argv = [
            "sync",
            "--skills-root",
            str(self.skills_root),
            "--home",
            str(self.home),
        ]
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = linker.main(argv, self.environ)

        report = json.loads(stdout.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(report["config"]["path"], str(xdg))
        self.assertIn(str(fallback), stderr.getvalue())

    def test_init_config_dry_run_selects_agents_and_detected_harnesses(self) -> None:
        """Initializer omits deprecated Codex routing without writing anything."""

        self.create_skill("alpha")
        self.create_skill("beta")
        (self.home / ".claude").mkdir()
        (self.home / ".codex").mkdir()

        report, status = linker.run_init_config(
            self.args(operation="init-config", dry_run=True), self.environ
        )

        self.assertEqual(status, 0)
        self.assertFalse(self.config_path().exists())
        self.assertFalse(report["applied"])
        self.assertEqual(report["config"]["harnesses"], ["agents", "claude"])
        content = tomllib.loads(report["config"]["content"])
        self.assertEqual(content["harness"]["agents"]["skills"], ["alpha", "beta"])
        self.assertEqual(content["harness"]["claude"]["skills"], ["alpha", "beta"])
        self.assertEqual(report["summary"]["configs_planned"], 1)

    def test_init_config_creates_xdg_config_and_refuses_overwrite(self) -> None:
        """Initializer writes once to XDG and never replaces an active config."""

        self.create_skill("alpha")

        report, status = linker.run_init_config(
            self.args(operation="init-config"), self.environ
        )

        self.assertEqual(status, 0)
        self.assertEqual(report["config"]["path"], str(self.config_path()))
        self.assertTrue(self.config_path().is_file())
        self.assertTrue(report["applied"])
        self.assertEqual(report["summary"]["configs_created"], 1)
        self.assertFalse((self.home / ".agents" / "skills").exists())
        with self.assertRaises(linker.InputError):
            linker.run_init_config(self.args(operation="init-config"), self.environ)

    def test_init_config_honors_an_explicit_nonexistent_path(self) -> None:
        """An explicit initializer path replaces the automatic XDG destination."""

        self.create_skill("alpha")
        explicit = self.root / "routing" / "custom.toml"

        report, status = linker.run_init_config(
            self.args(operation="init-config", config=str(explicit)), self.environ
        )

        self.assertEqual(status, 0)
        self.assertEqual(report["config"]["path"], str(explicit))
        self.assertTrue(explicit.is_file())
        self.assertFalse(self.config_path().exists())

    def test_init_config_keeps_always_route_when_destination_conflicts(self) -> None:
        """The generated policy retains agents so sync can report its conflict."""

        self.create_skill("alpha")
        (self.home / ".agents").mkdir()
        (self.home / ".agents" / "skills").write_text("conflict\n", encoding="utf-8")

        report, status = linker.run_init_config(
            self.args(operation="init-config", dry_run=True), self.environ
        )

        self.assertEqual(status, 0)
        self.assertIn("agents", report["config"]["harnesses"])

    def test_config_rewrite_preserves_existing_file_mode(self) -> None:
        """Atomic canonicalization retains the original config permissions."""

        for name in ("alpha", "beta"):
            self.create_skill(name)
        path = self.write_config(
            """schema_version = 1
[harness.agents]
mode = "always"
new_skills = "link"
skills = ["alpha"]
"""
        )
        path.chmod(0o640)

        _, status = self.run_sync()

        self.assertEqual(status, 0)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)

    def test_semantic_change_uses_atomic_canonical_serialization(self) -> None:
        """A routing change rewrites every table and array in stable sorted form."""

        for name in ("alpha", "beta"):
            self.create_skill(name)
        path = self.write_config(
            """# Canonical rewriting intentionally removes this comment.
schema_version = 1

[harness.zeta]
mode = "always"
skills_dir = "~/.zeta/skills"
new_skills = "link"
skills = ["beta", "beta"]
exclude_skills = []

[harness.agents]
mode = "always"
new_skills = "ignore"
skills = ["beta", "alpha", "alpha"]
exclude_skills = []
"""
        )
        real_replace = os.replace

        with mock.patch.object(
            linker.os, "replace", side_effect=real_replace
        ) as replace:
            _, status = self.run_sync()

        text = path.read_text(encoding="utf-8")
        user = linker.resolve_user_directories(self.home, self.environ)
        loaded = linker.load_config(path, user, linker.builtin_registry(user))
        self.assertEqual(status, 0)
        replace.assert_called_once()
        self.assertEqual(text, linker.serialize_config(loaded.routes))
        self.assertNotIn("Canonical rewriting", text)
        self.assertLess(text.index("[harness.agents]"), text.index("[harness.zeta]"))
        parsed = tomllib.loads(text)
        self.assertEqual(parsed["harness"]["agents"]["skills"], ["alpha", "beta"])
        self.assertEqual(parsed["harness"]["zeta"]["skills"], ["alpha", "beta"])

    def test_config_write_failure_returns_complete_plan_without_harness_mutation(
        self,
    ) -> None:
        """A failed desired-state write prevents every planned link change."""

        for name in ("alpha", "beta"):
            self.create_skill(name)
        path = self.write_config(
            """schema_version = 1

[harness.agents]
mode = "always"
new_skills = "link"
skills = ["alpha"]
"""
        )
        before = path.read_bytes()

        with mock.patch.object(
            linker, "atomic_write", side_effect=PermissionError("read-only config")
        ):
            report, status = self.run_sync()

        self.assertEqual(status, 1)
        self.assertFalse(report["applied"])
        self.assertEqual(report["config"]["write_status"], "error")
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse((self.home / ".agents").exists())
        actions = self.harness(report, "agents")["actions"]
        self.assertEqual(
            {(action["action"], action["skill"]) for action in actions},
            {("would-create", "alpha"), ("would-create", "beta")},
        )
        self.assertEqual(report["errors"][0]["scope"], "config")

    def test_config_write_precedes_application_of_the_complete_plan(self) -> None:
        """Desired state is durable before the first target directory is created."""

        for name in ("alpha", "beta"):
            self.create_skill(name)
        self.write_config(
            """schema_version = 1

[harness.agents]
mode = "always"
new_skills = "link"
skills = ["alpha"]
"""
        )
        real_atomic_write = linker.atomic_write
        observed: list[str] = []

        def guarded_write(path: Path, content: str) -> None:
            self.assertFalse((self.home / ".agents").exists())
            observed.append("config-written")
            real_atomic_write(path, content)

        with mock.patch.object(linker, "atomic_write", side_effect=guarded_write):
            report, status = self.run_sync()

        self.assertEqual(status, 0)
        self.assertEqual(observed, ["config-written"])
        self.assertTrue(report["applied"])
        self.assertTrue((self.home / ".agents" / "skills" / "alpha").is_symlink())
        self.assertTrue((self.home / ".agents" / "skills" / "beta").is_symlink())

    def test_link_failure_leaves_updated_desired_state_retryable(self) -> None:
        """A later operational failure does not roll back a successful config update."""

        for name in ("alpha", "beta"):
            self.create_skill(name)
        path = self.write_config(
            """schema_version = 1

[harness.agents]
mode = "always"
new_skills = "link"
skills = ["alpha"]
"""
        )

        with mock.patch.object(
            linker.os, "symlink", side_effect=PermissionError("developer mode required")
        ):
            report, status = self.run_sync()

        parsed = tomllib.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(status, 1)
        self.assertTrue(report["config"]["updated"])
        self.assertEqual(report["config"]["write_status"], "updated")
        self.assertEqual(parsed["harness"]["agents"]["skills"], ["alpha", "beta"])
        self.assertEqual(report["summary"]["errors"], 2)

    def test_relative_path_failure_has_no_absolute_fallback(self) -> None:
        """Cross-volume relative-path failure is reported without another link type."""

        self.create_skill("alpha")
        with mock.patch.object(
            linker.os.path, "relpath", side_effect=ValueError("different drives")
        ):
            report, status = self.run_sync()

        self.assertEqual(status, 1)
        self.assertFalse((self.home / ".agents" / "skills" / "alpha").exists())
        actions = self.harness(report, "agents")["actions"]
        self.assertIn("cross-volume", actions[0]["message"])

    def test_symlink_permission_failure_is_aggregated(self) -> None:
        """Platform symlink denial is actionable and leaves no copied fallback."""

        self.create_skill("alpha")
        with mock.patch.object(
            linker.os, "symlink", side_effect=PermissionError("developer mode required")
        ):
            report, status = self.run_sync()

        self.assertEqual(status, 1)
        actions = self.harness(report, "agents")["actions"]
        self.assertIn("developer mode required", actions[0]["message"])

    def test_main_emits_structured_invalid_input_and_exit_two(self) -> None:
        """CLI input failures remain machine-readable as well as diagnostic."""

        stdout = io.StringIO()
        stderr = io.StringIO()
        missing = self.root / "missing-config.toml"
        argv = [
            "sync",
            "--skills-root",
            str(self.skills_root),
            "--home",
            str(self.home),
            "--config",
            str(missing),
        ]

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = linker.main(argv, self.environ)

        self.assertEqual(status, 2)
        report = json.loads(stdout.getvalue())
        self.assertEqual(report["status"], "invalid-input")
        self.assertEqual(report["summary"], {"conflicts": 0, "errors": 1})
        self.assertIn("explicit config does not exist", stderr.getvalue())

    def test_main_reports_aggregate_conflicts_as_json_and_diagnostics(self) -> None:
        """A partial sync exposes the same conflict in both output channels."""

        self.create_skill("alpha")
        target = self.home / ".agents" / "skills"
        target.mkdir(parents=True)
        (target / "alpha").write_text("preserve\n", encoding="utf-8")
        stdout = io.StringIO()
        stderr = io.StringIO()
        argv = [
            "sync",
            "--skills-root",
            str(self.skills_root),
            "--home",
            str(self.home),
        ]

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = linker.main(argv, self.environ)

        report = json.loads(stdout.getvalue())
        self.assertEqual(status, 1)
        self.assertEqual(report["config"]["path"], None)
        self.assertEqual(report["summary"]["conflicts"], 1)
        self.assertEqual(len(report["conflicts"]), 1)
        self.assertEqual(report["errors"], [])
        self.assertIn("agents/alpha", stderr.getvalue())
        self.assertEqual((target / "alpha").read_text(encoding="utf-8"), "preserve\n")

    def test_main_emits_structured_argparse_failures(self) -> None:
        """Invalid command syntax also returns JSON and exit status two."""

        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = linker.main(["sync", "--unknown-option"], self.environ)

        self.assertEqual(status, 2)
        report = json.loads(stdout.getvalue())
        self.assertEqual(report["operation"], "sync")
        self.assertEqual(report["status"], "invalid-input")
        self.assertIn("unrecognized arguments", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
