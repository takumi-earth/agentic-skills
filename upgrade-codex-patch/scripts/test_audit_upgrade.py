#!/usr/bin/env python3
"""Exercise the audit CLI against real, disposable Git repositories."""

import hashlib
import json
import os
from difflib import unified_diff
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("audit_upgrade.py")
SCRATCH = Path(__file__).resolve().parents[2] / ".scratchpad/upgrade-codex-patch/tests"


class AuditUpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SCRATCH.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.repo = self.directory / "repo with spaces"
        self.repo.mkdir()
        self.git("init", "--quiet")
        self.write(
            "codex-rs/Cargo.toml",
            '[workspace]\nmembers = ["image"]\n[workspace.dependencies]\nzune-core = "=0.5.1"\n',
        )
        self.write(
            "codex-rs/image/Cargo.toml",
            '[package]\nname = "image-fixture"\nversion = "0.1.0"\n[dependencies]\nzune-core = { workspace = true }\n[target.\'cfg(windows)\'.build-dependencies]\nzune-core = { workspace = true }\n',
        )
        self.write("codex-rs/Cargo.lock", "old resolution\n")
        self.write("codex-rs/image/src/lib.rs", "before\n")
        self.write("unrelated.txt", "user content\n")
        self.write("large-untouched.txt", "untouched content\n" * 1000)
        self.git("add", ".")
        self.commit("baseline")
        self.git("tag", "rust-v0.1.0")
        self.write("codex-rs/image/src/lib.rs", "after\n")
        self.previous = self.directory / "previous.patch"
        self.previous.write_bytes(
            self.git(
                "diff", "--binary", "HEAD", "--", "codex-rs/image/src/lib.rs"
            ).stdout
        )
        self.write("codex-rs/image/src/lib.rs", "before\n")
        self.baseline = self.directory / "baseline.json"
        self.successor = self.directory / "successor.patch"
        self.selection = self.directory / "reviewed-selection.patch"
        self.selection.write_bytes(self.previous.read_bytes())

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.repo), *args],
            capture_output=True,
            check=True,
        )

    def commit(self, message):
        self.git(
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            f"core.hooksPath={self.directory / 'empty-hooks'}",
            "commit",
            "--quiet",
            "-m",
            message,
        )

    def write(self, name, text):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def run_helper(self, *args, expected_exit=0):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            result.returncode, expected_exit, result.stdout + result.stderr
        )
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def capture(self, output=None, extra=()):
        args = [
            "snapshot",
            "--repo",
            self.repo,
            "--previous-patch",
            self.previous,
            "--exclude",
            "codex-rs/Cargo.lock",
            *extra,
        ]
        if output is not None:
            args.extend(["--output", output])
        return self.run_helper(*args)

    def apply_and_export(self):
        self.git("apply", str(self.previous))
        self.write("codex-rs/Cargo.lock", "upgraded resolution\n")
        self.successor.write_bytes(
            self.git(
                "diff",
                "--binary",
                "--no-ext-diff",
                "HEAD",
                "--",
                "codex-rs/image/src/lib.rs",
            ).stdout
        )

    def audit(self, *extra, expected_exit=0):
        return self.run_helper(
            "audit",
            "--baseline",
            self.baseline,
            "--successor-patch",
            self.successor,
            "--selected-export",
            self.selection,
            "--scratch-root",
            self.directory,
            *extra,
            expected_exit=expected_exit,
        )

    def failed_conditions(self, report):
        return {
            check["condition"]
            for check in report["checks"]
            if check["status"] == "failed"
        }

    def test_snapshot_is_bounded_and_resolves_workspace_and_target_pins(self):
        state = (
            self.git("rev-parse", "HEAD").stdout,
            self.git("ls-files", "--stage", "-z").stdout,
            self.git("status", "--porcelain").stdout,
        )
        report = self.capture(self.baseline)
        self.assertEqual(json.loads(self.baseline.read_text()), report)
        self.assertEqual(report["tag"], "rust-v0.1.0")
        self.assertEqual(
            set(report["files"]),
            {
                "codex-rs/Cargo.toml",
                "codex-rs/Cargo.lock",
                "codex-rs/image/Cargo.toml",
                "codex-rs/image/src/lib.rs",
            },
        )
        self.assertEqual(
            report["observation"]["bytes_read"],
            sum((self.repo / name).stat().st_size for name in report["files"]),
        )
        self.assertEqual(
            report["exact_pins"],
            [
                {
                    "manifest": "codex-rs/Cargo.toml",
                    "table": "workspace.dependencies",
                    "dependency": "zune-core",
                    "requirement": "=0.5.1",
                    "source_manifest": "codex-rs/Cargo.toml",
                },
                {
                    "manifest": "codex-rs/image/Cargo.toml",
                    "table": "dependencies",
                    "dependency": "zune-core",
                    "requirement": "=0.5.1",
                    "source_manifest": "codex-rs/Cargo.toml",
                },
                {
                    "manifest": "codex-rs/image/Cargo.toml",
                    "table": "target.cfg(windows).build-dependencies",
                    "dependency": "zune-core",
                    "requirement": "=0.5.1",
                    "source_manifest": "codex-rs/Cargo.toml",
                },
            ],
        )
        self.assertEqual(
            state,
            (
                self.git("rev-parse", "HEAD").stdout,
                self.git("ls-files", "--stage", "-z").stdout,
                self.git("status", "--porcelain").stdout,
            ),
        )
        self.assertEqual(
            report["repo"], "~/" + self.repo.relative_to(Path.home()).as_posix()
        )

    def test_snapshot_allows_metadata_refresh_and_distinguishes_stat_from_content_changes(self):
        path = self.repo / "unrelated.txt"
        original = path.read_bytes()
        self.git("config", "diff.autoRefreshIndex", "true")
        self.git("update-index", "--refresh")
        index = self.repo / ".git/index"
        cache_before = index.read_bytes()
        staged_before = self.git("ls-files", "--stage", "-z").stdout
        stat = path.stat()
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))

        unchanged = self.capture()

        self.assertNotEqual(index.read_bytes(), cache_before)
        self.assertEqual(self.git("ls-files", "--stage", "-z").stdout, staged_before)
        self.assertEqual(unchanged["index_sha256"], hashlib.sha256(staged_before).hexdigest())
        self.assertNotIn("index_bytes_sha256", unchanged)
        self.assertEqual(unchanged["changed_paths"], [])
        self.assertNotIn("unrelated.txt", unchanged["files"])
        self.assertEqual(path.read_bytes(), original)

        self.write("unrelated.txt", "actual content change\n")
        changed = self.capture()

        self.assertEqual(self.git("ls-files", "--stage", "-z").stdout, staged_before)
        self.assertEqual(changed["changed_paths"], ["unrelated.txt"])
        self.assertEqual(
            changed["files"]["unrelated.txt"]["sha256"],
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )

    def test_snapshot_keeps_rename_binary_and_unusual_path_evidence_without_staging_changes(self):
        renamed = "renamed\tfile\nname.txt"
        (self.repo / "unrelated.txt").rename(self.repo / renamed)
        (self.repo / "large-untouched.txt").write_bytes(b"\0binary change\xff")
        self.git("add", ".")
        before = self.git("ls-files", "--stage", "-z").stdout

        report = self.capture()

        self.assertEqual(self.git("ls-files", "--stage", "-z").stdout, before)
        self.assertEqual(
            report["changed_paths"], ["large-untouched.txt", renamed, "unrelated.txt"]
        )
        self.assertIsNone(report["files"]["unrelated.txt"])
        for name in ("large-untouched.txt", renamed):
            self.assertEqual(
                report["files"][name]["sha256"],
                hashlib.sha256((self.repo / name).read_bytes()).hexdigest(),
            )

    def test_changes_separate_dependency_and_source_fallout(self):
        before = self.capture(self.baseline)
        self.apply_and_export()
        after = self.directory / "after.json"
        self.capture(after)
        report = self.run_helper("changes", "--before", self.baseline, "--after", after)
        self.assertEqual(
            report,
            {
                "schema_version": 1,
                "kind": "changes",
                "status": "passed",
                "repo": "~/" + self.repo.relative_to(Path.home()).as_posix(),
                "changed_paths": ["codex-rs/Cargo.lock", "codex-rs/image/src/lib.rs"],
                "dependency_files": ["codex-rs/Cargo.lock"],
                "other_paths": ["codex-rs/image/src/lib.rs"],
                "head_unchanged": True,
                "index_unchanged": True,
                "previous_patch_unchanged": True,
                "new_untracked_paths": [],
                "checks": [
                    {
                        "condition": condition,
                        "expected": before[field],
                        "received": before[field],
                        "status": "passed",
                    }
                    for condition, field in (
                        ("HEAD is unchanged", "head"),
                        ("index entries are unchanged", "index_sha256"),
                        ("previous patch is unchanged", "previous_patch"),
                    )
                ],
            },
        )

    def test_successful_audit_preserves_user_edits_and_index(self):
        self.write("unrelated.txt", "existing user edit\n")
        self.capture(self.baseline)
        self.apply_and_export()
        state = (
            self.git("ls-files", "--stage", "-z").stdout,
            self.git("diff", "HEAD").stdout,
        )
        report = self.audit()
        self.assertEqual(report["status"], "passed")
        self.assertEqual(
            report["successor"]["sha256"],
            hashlib.sha256(self.successor.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            report["comparison"],
            {
                "common_files": 1,
                "identical_edit_streams": 1,
                "differing_paths": [],
                "old_only_paths": [],
                "new_only_paths": [],
                "identical_hunk_edit_streams": 1,
            },
        )
        self.assertEqual(
            {name: value["status"] for name, value in report["applicability"].items()},
            {"cached": "passed", "target_base": "passed"},
        )
        self.assertEqual(report["excluded_paths"], ["codex-rs/Cargo.lock"])
        self.assertEqual(
            state,
            (
                self.git("ls-files", "--stage", "-z").stdout,
                self.git("diff", "HEAD").stdout,
            ),
        )

    def test_index_cache_refresh_is_accepted_by_comparison_and_final_audit(self):
        baseline = self.capture(self.baseline)
        index = self.repo / ".git/index"
        cache_before = index.read_bytes()
        staged_before = self.git("ls-files", "--stage", "-z").stdout
        # Historical evidence can contain a cache digest; it is not a staging gate.
        baseline["index_bytes_sha256"] = hashlib.sha256(cache_before).hexdigest()
        self.baseline.write_text(json.dumps(baseline), encoding="utf-8")
        path = self.repo / "unrelated.txt"
        stat = path.stat()
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))
        self.git("update-index", "--refresh")
        self.assertNotEqual(index.read_bytes(), cache_before)
        self.assertEqual(self.git("ls-files", "--stage", "-z").stdout, staged_before)
        self.apply_and_export()
        after = self.directory / "after.json"
        self.capture(after)

        comparison = self.run_helper(
            "changes", "--before", self.baseline, "--after", after
        )
        report = self.audit()

        self.assertEqual(comparison["status"], "passed")
        self.assertTrue(comparison["index_unchanged"])
        self.assertEqual(self.failed_conditions(comparison), set())
        self.assertEqual(report["status"], "passed")
        self.assertEqual(self.failed_conditions(report), set())
        self.assertEqual(self.git("ls-files", "--stage", "-z").stdout, staged_before)

    def test_non_pristine_index_is_preserved_and_cached_check_is_not_run(self):
        self.write("unrelated.txt", "staged user edit\n")
        self.git("add", "unrelated.txt")
        self.capture(self.baseline)
        self.apply_and_export()
        index = self.git("ls-files", "--stage", "-z").stdout
        report = self.audit()
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["applicability"]["cached"]["status"], "not-run")
        self.assertEqual(report["applicability"]["target_base"]["status"], "passed")
        self.assertEqual(index, self.git("ls-files", "--stage", "-z").stdout)

    def test_already_applied_predecessor_can_carry_an_authorized_addition(self):
        self.git("apply", str(self.previous))
        baseline = self.capture(self.baseline)
        self.assertEqual(
            baseline["predecessor_worktree_export_sha256"],
            baseline["previous_patch"]["sha256"],
        )
        self.write("codex-rs/image/src/lib.rs", "after\nauthorized addition\n")
        self.successor.write_bytes(
            self.git(
                "diff",
                "--binary",
                "--no-ext-diff",
                "HEAD",
                "--",
                "codex-rs/image/src/lib.rs",
            ).stdout
        )
        self.selection.write_bytes(self.successor.read_bytes())
        index = self.git("ls-files", "--stage", "-z").stdout
        report = self.audit()
        self.assertEqual(report["status"], "passed")
        self.assertEqual(
            {name: value["status"] for name, value in report["applicability"].items()},
            {"cached": "passed", "target_base": "passed"},
        )
        self.assertEqual(index, self.git("ls-files", "--stage", "-z").stdout)

    def test_already_applied_predecessor_with_extra_user_edits_is_unresolved(self):
        self.git("apply", str(self.previous))
        self.write("codex-rs/image/src/lib.rs", "after\nexisting user addition\n")
        self.capture(self.baseline)
        self.successor.write_bytes(
            self.git(
                "diff",
                "--binary",
                "--no-ext-diff",
                "HEAD",
                "--",
                "codex-rs/image/src/lib.rs",
            ).stdout
        )
        report = self.audit(expected_exit=1)
        self.assertEqual(
            self.failed_conditions(report),
            {
                "pre-existing export edits have recorded predecessor provenance",
                "successor bytes equal the reviewed hunk selection",
            },
        )

    def test_older_snapshot_without_predecessor_export_digest_remains_supported(self):
        baseline = self.capture()
        del baseline["predecessor_worktree_export_sha256"]
        self.baseline.write_text(json.dumps(baseline), encoding="utf-8")
        self.apply_and_export()
        report = self.audit()
        self.assertEqual(report["status"], "passed")

    def test_audit_rejects_excluded_lockfile_in_the_artifact(self):
        self.capture(self.baseline)
        self.apply_and_export()
        self.successor.write_bytes(
            self.git("diff", "--binary", "--no-ext-diff", "HEAD").stdout
        )
        report = self.audit(expected_exit=1)
        self.assertEqual(
            self.failed_conditions(report),
            {
                "patch paths belong to the intended set",
                "successor bytes equal the reviewed hunk selection",
            },
        )

    def test_mutated_predecessor_fails_audit_and_snapshot_comparison(self):
        self.capture(self.baseline)
        self.apply_and_export()
        self.previous.write_bytes(self.previous.read_bytes() + b"\n")
        report = self.audit(expected_exit=1)
        self.assertEqual(
            self.failed_conditions(report), {"previous patch is unchanged"}
        )
        after = self.directory / "after.json"
        self.capture(after)
        delta = self.run_helper(
            "changes", "--before", self.baseline, "--after", after, expected_exit=1
        )
        self.assertEqual(delta["previous_patch_unchanged"], False)
        self.assertEqual(
            [check for check in delta["checks"] if check["status"] == "failed"],
            [
                {
                    "condition": "previous patch is unchanged",
                    "expected": json.loads(self.baseline.read_text())["previous_patch"],
                    "received": json.loads(after.read_text())["previous_patch"],
                    "status": "failed",
                }
            ],
        )

    def test_untracked_excluded_command_fallout_is_accounted_for(self):
        self.capture(self.baseline, extra=("--exclude", "codex-rs/image/Cargo.lock"))
        self.apply_and_export()
        self.write("codex-rs/image/Cargo.lock", "generated crate resolution\n")
        report = self.audit()
        self.assertEqual(report["status"], "passed")
        self.assertEqual(
            report["excluded_paths"],
            ["codex-rs/Cargo.lock", "codex-rs/image/Cargo.lock"],
        )

    def test_lost_unrelated_user_edit_fails_preservation(self):
        self.write("unrelated.txt", "existing user edit\n")
        self.capture(self.baseline)
        self.apply_and_export()
        self.write("unrelated.txt", "user content\n")
        report = self.audit(expected_exit=1)
        self.assertEqual(
            self.failed_conditions(report),
            {"unrelated pre-existing edits are preserved"},
        )

    def test_help_and_invalid_arguments_do_not_publish_reports(self):
        output = self.directory / "uncreated" / "report.json"
        help_result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"], capture_output=True, check=False
        )
        invalid_result = subprocess.run(
            [sys.executable, str(SCRIPT), "snapshot", "--output", str(output)],
            capture_output=True,
            check=False,
        )
        self.assertEqual((help_result.returncode, help_result.stderr), (0, b""))
        self.assertEqual((invalid_result.returncode, invalid_result.stdout), (2, b""))
        self.assertFalse(output.parent.exists())

    def test_untracked_additions_are_reported_instead_of_silently_omitted(self):
        self.capture(self.baseline)
        self.apply_and_export()
        self.write("codex-rs/image/src/new.rs", "new behavior\n")
        report = self.audit("--include", "codex-rs/image/src/new.rs", expected_exit=1)
        self.assertEqual(
            self.failed_conditions(report),
            {
                "authorized untracked additions are included in the selected export",
            },
        )
        self.assertEqual(
            self.git("ls-files", "--others", "--exclude-standard").stdout,
            b"codex-rs/image/src/new.rs\n",
        )

    def test_preexisting_hunks_in_exported_paths_are_not_claimed_as_carried_work(self):
        self.write("codex-rs/image/src/lib.rs", "before\nuser addition\n")
        self.capture(self.baseline)
        self.write("codex-rs/image/src/lib.rs", "after\nuser addition\n")
        self.successor.write_bytes(
            self.git(
                "diff",
                "--binary",
                "--no-ext-diff",
                "HEAD",
                "--",
                "codex-rs/image/src/lib.rs",
            ).stdout
        )
        report = self.audit(expected_exit=1)
        self.assertEqual(
            self.failed_conditions(report),
            {
                "pre-existing export edits have recorded predecessor provenance",
                "successor bytes equal the reviewed hunk selection",
            },
        )

    def test_index_change_fails_without_unstaging_it(self):
        self.capture(self.baseline)
        self.apply_and_export()
        self.git("add", "codex-rs/Cargo.lock")
        index = self.git("ls-files", "--stage", "-z").stdout
        report = self.audit(expected_exit=1)
        self.assertEqual(
            self.failed_conditions(report),
            {"index entries are unchanged"},
        )
        self.assertEqual(index, self.git("ls-files", "--stage", "-z").stdout)

    def test_staged_mode_change_fails_comparison_and_audit_without_repairing_staging(self):
        scope = ("--include", "unrelated.txt")
        self.capture(self.baseline, extra=scope)
        original = (self.repo / "unrelated.txt").read_bytes()
        self.apply_and_export()
        self.git("update-index", "--chmod=+x", "unrelated.txt")
        staged = self.git("ls-files", "--stage", "-z").stdout
        selected = self.git("diff", "--cached", "--binary").stdout
        after = self.directory / "after.json"
        self.capture(after, extra=scope)

        comparison = self.run_helper(
            "changes", "--before", self.baseline, "--after", after, expected_exit=1
        )
        report = self.audit(expected_exit=1)

        self.assertFalse(comparison["index_unchanged"])
        self.assertEqual(self.failed_conditions(comparison), {"index entries are unchanged"})
        self.assertEqual(self.failed_conditions(report), {"index entries are unchanged"})
        self.assertEqual(self.git("ls-files", "--stage", "-z").stdout, staged)
        self.assertEqual(self.git("diff", "--cached", "--binary").stdout, selected)
        self.assertEqual((self.repo / "unrelated.txt").read_bytes(), original)

    def test_report_publication_preserves_existing_outputs_and_refuses_repo_outputs(
        self,
    ):
        self.baseline.write_text("existing evidence\n")
        original = self.baseline.read_bytes()
        self.run_helper(
            "snapshot",
            "--repo",
            self.repo,
            "--previous-patch",
            self.previous,
            "--output",
            self.baseline,
            expected_exit=2,
        )
        self.assertEqual(self.baseline.read_bytes(), original)
        output = self.repo / "report.json"
        report = self.run_helper(
            "snapshot",
            "--repo",
            self.repo,
            "--previous-patch",
            self.previous,
            "--output",
            output,
            expected_exit=2,
        )
        self.assertEqual(
            report["error"]["condition"], "evidence is outside the audited repository"
        )
        self.assertFalse(output.exists())

    def test_output_parent_symlink_cannot_publish_into_the_audited_repo(self):
        parent = self.directory / "linked-parent"
        try:
            parent.symlink_to(self.repo, target_is_directory=True)
        except OSError as error:
            self.skipTest(str(error))
        output = parent / "report.json"
        self.run_helper(
            "snapshot",
            "--repo",
            self.repo,
            "--previous-patch",
            self.previous,
            "--output",
            output,
            expected_exit=2,
        )
        self.assertFalse(output.exists())

    def test_invalid_snapshot_is_a_structured_error(self):
        self.baseline.write_text(
            '{"schema_version": 1, "kind": "snapshot", "files": []}'
        )
        report = self.run_helper(
            "audit",
            "--baseline",
            self.baseline,
            "--successor-patch",
            self.successor,
            "--selected-export",
            self.selection,
            "--scratch-root",
            self.directory,
            expected_exit=2,
        )
        self.assertEqual(
            report["error"]["condition"], "snapshot schema is supported and complete"
        )

    def test_scope_changes_between_snapshots_require_explicit_resolution(self):
        self.capture(self.baseline)
        after = self.directory / "after.json"
        self.capture(after, extra=("--include", "codex-rs/image/src/new.rs"))
        report = self.run_helper(
            "changes", "--before", self.baseline, "--after", after, expected_exit=2
        )
        self.assertEqual(
            report["error"],
            {
                "condition": "snapshot scopes match",
                "expected": {"included_paths": []},
                "received": {"included_paths": ["codex-rs/image/src/new.rs"]},
            },
        )

    def test_reviewed_staged_fields_exclude_automatic_versions_in_the_same_manifest(
        self,
    ):
        base = (
            '[workspace]\nmembers = ["image"]\nresolver = "2"\n'
            '[workspace.dependencies]\nzune-core = "0.5.1"\n'
            'ordinary = "1.0"\n'
            'configured = { version = "2.0", features = ["old"] }\n'
        )
        selected = (
            base.replace('resolver = "2"', 'resolver = "3"')
            .replace('zune-core = "0.5.1"', 'zune-core = "=0.5.1"')
            .replace('features = ["old"]', 'features = ["new"]')
        )
        self.write("codex-rs/Cargo.toml", base)
        self.git("add", "codex-rs/Cargo.toml")
        self.commit("manifest base")
        self.write("codex-rs/Cargo.toml", selected)
        self.write("codex-rs/image/src/lib.rs", "after\n")
        self.git("add", "codex-rs/Cargo.toml", "codex-rs/image/src/lib.rs")
        self.previous.write_bytes(
            self.git("diff", "--cached", "--binary", "HEAD").stdout
        )
        self.selection.write_bytes(self.previous.read_bytes())
        upgraded = selected.replace('ordinary = "1.0"', 'ordinary = "1.9"').replace(
            'version = "2.0"', 'version = "2.8"'
        )
        self.write("codex-rs/Cargo.toml", upgraded)
        baseline = self.capture(self.baseline)
        self.assertEqual(
            baseline["predecessor_index_export_sha256"],
            baseline["previous_patch"]["sha256"],
        )
        state = (
            self.git("ls-files", "--stage", "-z").stdout,
            self.git("diff", "--cached", "--binary").stdout,
            self.git("diff", "--binary").stdout,
            tomllib.loads((self.repo / "codex-rs/Cargo.toml").read_text()),
        )
        self.successor.write_bytes(self.selection.read_bytes())
        report = self.audit()
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["applicability"]["target_base"]["status"], "passed")
        self.assertEqual(
            state,
            (
                self.git("ls-files", "--stage", "-z").stdout,
                self.git("diff", "--cached", "--binary").stdout,
                self.git("diff", "--binary").stdout,
                tomllib.loads((self.repo / "codex-rs/Cargo.toml").read_text()),
            ),
        )
        self.successor.write_bytes(self.git("diff", "--binary", "HEAD").stdout)
        rejected = self.audit(expected_exit=1)
        self.assertEqual(
            self.failed_conditions(rejected),
            {"successor bytes equal the reviewed hunk selection"},
        )

    def test_selected_export_can_include_an_authorized_untracked_source_without_staging(
        self,
    ):
        new_source = "codex-rs/image/src/new.rs"
        self.capture(self.baseline, extra=("--include", new_source))
        self.apply_and_export()
        self.write(new_source, "pub fn answer() -> u8 { 42 }\n")
        addition = (
            f"diff --git a/{new_source} b/{new_source}\nnew file mode 100644\n"
            + "".join(
                unified_diff(
                    [],
                    (self.repo / new_source).read_text().splitlines(keepends=True),
                    fromfile="/dev/null",
                    tofile=f"b/{new_source}",
                )
            )
        ).encode()
        self.selection.write_bytes(self.selection.read_bytes() + addition)
        self.successor.write_bytes(self.selection.read_bytes())
        index = self.git("ls-files", "--stage", "-z").stdout
        report = self.audit("--include", new_source)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["applicability"]["target_base"]["status"], "passed")
        self.assertEqual(self.git("ls-files", "--stage", "-z").stdout, index)
        self.assertEqual(
            self.git("ls-files", "--others", "--exclude-standard").stdout,
            new_source.encode() + b"\n",
        )

    def test_audit_has_no_implicit_whole_worktree_export_fallback(self):
        self.capture(self.baseline)
        self.apply_and_export()
        index = self.git("ls-files", "--stage", "-z").stdout
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "audit",
                "--baseline",
                str(self.baseline),
                "--successor-patch",
                str(self.successor),
                "--scratch-root",
                str(self.directory),
            ],
            capture_output=True,
            check=False,
        )
        self.assertEqual((result.returncode, result.stdout), (2, b""))
        self.assertIn(b"--selected-export", result.stderr)
        self.assertEqual(self.git("ls-files", "--stage", "-z").stdout, index)

    def test_malformed_new_digest_fields_are_structured_input_failures(self):
        baseline = self.capture()
        for field in (
            "predecessor_worktree_export_sha256",
            "predecessor_index_export_sha256",
        ):
            with self.subTest(field=field):
                invalid = {**baseline, field: []}
                self.baseline.write_text(json.dumps(invalid), encoding="utf-8")
                report = self.audit(expected_exit=2)
                self.assertEqual(
                    report["error"],
                    {
                        "condition": "snapshot export/index digest is valid",
                        "expected": {
                            "field": field,
                            "value": "SHA-256 or an older snapshot without this field",
                        },
                        "received": [],
                    },
                )


if __name__ == "__main__":
    unittest.main()
