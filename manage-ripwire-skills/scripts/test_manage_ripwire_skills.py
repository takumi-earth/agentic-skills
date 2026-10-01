#!/usr/bin/env python3
"""Exercise real Git updates, archived bases, guarded acknowledgement, and entrypoints."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).with_name("manage_ripwire_skills.py")
spec = importlib.util.spec_from_file_location("manager", SCRIPT)
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)
SCRATCH = Path.home() / "agentic-skills/.scratchpad"


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.upstream = self.root / "upstream"
        self.upstream.mkdir()
        self.canonical = self.root / "canonical"
        self.canonical.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Fixture")
        for name in ("ripwire-alpha", "ripwire-beta"):
            self.package(name, "original")
        (self.upstream / "LICENSE").write_text("fixture notice\n")
        self.commit()
        self.original_oid = self.git("rev-parse", "HEAD").decode().strip()
        for name in ("ripwire-alpha", "ripwire-beta"):
            shutil.copytree(self.upstream / "skills" / name, self.canonical / name)
            (self.canonical / name / "LICENSE.upstream").write_text("fixture notice\n")
        manager.initialize(self.canonical, self.upstream, "HEAD")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.upstream), *args], check=True, capture_output=True).stdout

    def package(self, name, body):
        p = self.upstream / "skills" / name
        p.mkdir(parents=True, exist_ok=True)
        (p / "SKILL.md").write_text(f"---\nname: {name}\ndescription: fixture\n---\n{body}\n")
        return p

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-qm", "fixture change")

    def decisions(self, report, deferred=()):
        return {"packages": [{"name": row["name"], "disposition": "deferred" if row["name"] in deferred else "accepted",
                              "reason": "reviewed fixture change; canonical behavior retained",
                              "evidence": ["ripwire-alpha/SKILL.md"]}
                             for row in report["packages"] if row["status"] != "upstream-current"]}

    def test_check_does_not_change_customized_ports_or_baseline(self):
        local = self.canonical / "ripwire-alpha/SKILL.md"
        local.write_text(local.read_text() + "local policy\n")
        baseline = manager.state_path(self.canonical).read_bytes()
        body = local.read_bytes()
        report = manager.compare(self.canonical, self.upstream, "HEAD")
        self.assertEqual(report["status"], "upstream-current")
        self.assertTrue(report["packages"][0]["local_customized"])
        self.assertEqual(local.read_bytes(), body)
        self.assertEqual(manager.state_path(self.canonical).read_bytes(), baseline)

    def test_three_way_change_preserves_local_reference_split(self):
        self.package("ripwire-alpha", "upstream addition")
        self.commit()
        local = self.canonical / "ripwire-alpha/SKILL.md"
        local.write_text("---\nname: ripwire-alpha\ndescription: customized\n---\nSee reference.\n")
        (local.parent / "reference.md").write_text("local procedure\n")
        before = local.read_bytes()
        report = manager.compare(self.canonical, self.upstream, "HEAD")
        row = report["packages"][0]
        self.assertEqual(row["status"], "review-required")
        self.assertEqual(row["changes"][0]["kind"], "both-changed")
        manager.acknowledge(self.canonical, self.upstream, report, self.decisions(report))
        self.assertEqual(local.read_bytes(), before)
        self.assertEqual((local.parent / "reference.md").read_text(), "local procedure\n")
        self.assertEqual(manager.compare(self.canonical, self.upstream, "HEAD")["status"], "upstream-current")

    def test_partial_acknowledgement_keeps_deferred_package_pending(self):
        self.package("ripwire-alpha", "new alpha")
        self.package("ripwire-beta", "new beta")
        self.commit()
        report = manager.compare(self.canonical, self.upstream, "HEAD")
        result = manager.acknowledge(self.canonical, self.upstream, report, self.decisions(report, ("ripwire-beta",)))
        self.assertEqual(result["status"], "partially-acknowledged")
        self.assertEqual(result["deferred"], ["ripwire-beta"])
        rows = manager.compare(self.canonical, self.upstream, "HEAD")["packages"]
        self.assertEqual([r["name"] for r in rows if r["status"] == "review-required"], ["ripwire-beta"])

    def test_all_deferred_is_no_baseline_write(self):
        self.package("ripwire-alpha", "changed")
        self.commit()
        before = manager.state_path(self.canonical).read_bytes()
        report = manager.compare(self.canonical, self.upstream, "HEAD")
        result = manager.acknowledge(self.canonical, self.upstream, report, self.decisions(report, ("ripwire-alpha",)))
        self.assertEqual(result["status"], "deferred")
        self.assertFalse(result["baseline_written"])
        self.assertEqual(manager.state_path(self.canonical).read_bytes(), before)

    def test_stale_local_and_upstream_reports_refuse_without_write(self):
        self.package("ripwire-alpha", "new")
        self.commit()
        report = manager.compare(self.canonical, self.upstream, "HEAD")
        before = manager.state_path(self.canonical).read_bytes()
        local = self.canonical / "ripwire-alpha/SKILL.md"
        local.write_text(local.read_text() + "later local edit\n")
        with self.assertRaises(manager.StateError):
            manager.acknowledge(self.canonical, self.upstream, report, self.decisions(report))
        self.assertEqual(manager.state_path(self.canonical).read_bytes(), before)
        report = manager.compare(self.canonical, self.upstream, "HEAD")
        self.package("ripwire-alpha", "newer upstream")
        self.commit()
        with self.assertRaises(manager.StateError):
            manager.acknowledge(self.canonical, self.upstream, report, self.decisions(report))
        self.assertEqual(manager.state_path(self.canonical).read_bytes(), before)

    def test_new_package_is_reported_and_requires_canonical_adoption(self):
        self.package("ripwire-gamma", "new package")
        self.commit()
        report = manager.compare(self.canonical, self.upstream, "HEAD")
        self.assertEqual(next(r for r in report["packages"] if r["name"] == "ripwire-gamma")["status"], "new-upstream-package")
        with self.assertRaises(manager.StateError):
            manager.acknowledge(self.canonical, self.upstream, report, self.decisions(report))
        self.assertFalse((self.canonical / "ripwire-gamma").exists())

    def test_removed_upstream_package_retains_canonical_capability(self):
        shutil.rmtree(self.upstream / "skills/ripwire-beta")
        self.commit()
        report = manager.compare(self.canonical, self.upstream, "HEAD")
        manager.acknowledge(self.canonical, self.upstream, report, self.decisions(report))
        self.assertTrue((self.canonical / "ripwire-beta/SKILL.md").is_file())
        self.assertEqual(manager.compare(self.canonical, self.upstream, "HEAD")["status"], "upstream-current")

    def test_archive_corruption_refuses(self):
        path = manager.state_path(self.canonical)
        state = json.loads(path.read_text())
        state["packages"]["ripwire-alpha"]["files"]["SKILL.md"]["sha256"] = "wrong"
        path.write_text(json.dumps(state))
        with self.assertRaises(manager.StateError):
            manager.compare(self.canonical, self.upstream, "HEAD")

    def test_upstream_symlink_resource_is_refused(self):
        (self.upstream / "skills/ripwire-alpha/escape").symlink_to("../../outside")
        self.commit()
        with self.assertRaises(manager.StateError):
            manager.compare(self.canonical, self.upstream, "HEAD")

    def test_duplicate_or_missing_review_units_refuse(self):
        self.package("ripwire-alpha", "new")
        self.commit()
        report = manager.compare(self.canonical, self.upstream, "HEAD")
        for decisions in ({"packages": []}, {"packages": self.decisions(report)["packages"] * 2}):
            with self.assertRaises(manager.StateError):
                manager.acknowledge(self.canonical, self.upstream, report, decisions)

    def test_real_entrypoint_is_equivalent_when_copied_or_symlinked(self):
        package = SCRIPT.parent.parent
        copied = self.root / "copied-package"
        shutil.copytree(package, copied)
        linked = self.root / "linked-package"
        linked.symlink_to(package, target_is_directory=True)
        relative = self.root / "relative-package"
        relative.symlink_to(os.path.relpath(package, self.root), target_is_directory=True)
        protected = manager.local_files(self.root, "canonical")
        results = []
        for deployed in (package, copied, linked, relative):
            entry = deployed / "scripts/manage_ripwire_skills.py"
            p = subprocess.run([sys.executable, str(entry), "check", "--skills-root", str(self.canonical),
                                "--upstream-repo", str(self.upstream)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(p.stderr, "")
            results.append(json.loads(p.stdout))
            self.assertEqual(manager.local_files(self.root, "canonical"), protected)
        self.assertTrue(all(result == results[0] for result in results))

    def test_malformed_provenance_is_a_structured_cli_failure(self):
        path = manager.state_path(self.canonical)
        state = json.loads(path.read_text())
        state["packages"]["ripwire-alpha"]["upstream_oid"] = {"invalid": "object"}
        path.write_text(json.dumps(state))
        before = path.read_bytes()
        result = subprocess.run([sys.executable, str(SCRIPT), "check", "--skills-root", str(self.canonical),
                                 "--upstream-repo", str(self.upstream)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stderr)["status"], "failed")
        self.assertEqual(path.read_bytes(), before)

    def test_malformed_review_inputs_refuse_without_baseline_write(self):
        self.package("ripwire-alpha", "new")
        self.commit()
        report = manager.compare(self.canonical, self.upstream, "HEAD")
        valid = self.decisions(report)["packages"][0]
        before = manager.state_path(self.canonical).read_bytes()
        decisions = [[], {"packages": {}}, {"packages": [42]},
                     {"packages": [valid | {"disposition": {}}]},
                     {"packages": [valid | {"reason": 42}]},
                     {"packages": [valid | {"evidence": "ripwire-alpha/SKILL.md"}]}]
        for malformed in decisions:
            with self.subTest(decisions=malformed):
                with self.assertRaises(manager.StateError):
                    manager.acknowledge(self.canonical, self.upstream, report, malformed)
                self.assertEqual(manager.state_path(self.canonical).read_bytes(), before)

    def test_malformed_upstream_frontmatter_refuses(self):
        (self.upstream / "skills/ripwire-alpha/SKILL.md").write_text("missing frontmatter\n")
        self.commit()
        before = manager.state_path(self.canonical).read_bytes()
        with self.assertRaises(manager.StateError):
            manager.compare(self.canonical, self.upstream, "HEAD")
        self.assertEqual(manager.state_path(self.canonical).read_bytes(), before)

    def test_ref_moving_after_freshness_check_cannot_acknowledge_unreviewed_bytes(self):
        self.package("ripwire-alpha", "reviewed update")
        self.commit()
        report = manager.compare(self.canonical, self.upstream, "HEAD")
        compare = manager.compare

        def move_ref_after_check(*args):
            fresh = compare(*args)
            self.package("ripwire-alpha", "later unreviewed update")
            self.commit()
            return fresh

        with mock.patch.object(manager, "compare", side_effect=move_ref_after_check):
            manager.acknowledge(self.canonical, self.upstream, report, self.decisions(report))
        archived = manager.read_state(manager.state_path(self.canonical))["packages"]["ripwire-alpha"]
        self.assertEqual(archived["upstream_oid"], report["upstream_oid"])
        self.assertEqual(manager.compare(self.canonical, self.upstream, "HEAD")["status"], "review-required")

    def test_bad_output_destination_refuses_before_initialization(self):
        root = self.root / "uninitialized"
        root.mkdir()
        result = subprocess.run([sys.executable, str(SCRIPT), "initialize", "--skills-root", str(root),
                                 "--upstream-repo", str(self.upstream), "--output", str(self.root / "outside.json")],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((root / manager.STATE_RELATIVE).exists())
        self.assertFalse((self.root / "outside.json").exists())

    def test_missing_old_git_commit_uses_archived_base(self):
        self.package("ripwire-alpha", "later content")
        self.commit()
        old_object = self.upstream / ".git/objects" / self.original_oid[:2] / self.original_oid[2:]
        old_object.unlink()
        report = manager.compare(self.canonical, self.upstream, "HEAD")
        self.assertEqual(report["packages"][0]["status"], "review-required")
        self.assertEqual(report["packages"][0]["base_oid"], self.original_oid)

    def test_report_refresh_is_explicit_and_only_replaces_owned_report(self):
        output = self.canonical / ".scratchpad/manage-ripwire-skills/comparison.json"
        command = [sys.executable, str(SCRIPT), "check", "--skills-root", str(self.canonical),
                   "--upstream-repo", str(self.upstream), "--output", str(output)]
        first = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        before = output.read_bytes()
        refused = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(refused.returncode, 0)
        self.assertEqual(output.read_bytes(), before)
        refreshed = subprocess.run(command + ["--replace-report"], capture_output=True, text=True)
        self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
        output.write_text('{"unrelated": true}')
        refused = subprocess.run(command + ["--replace-report"], capture_output=True, text=True)
        self.assertNotEqual(refused.returncode, 0)
        self.assertEqual(json.loads(output.read_text()), {"unrelated": True})


if __name__ == "__main__":
    unittest.main()
