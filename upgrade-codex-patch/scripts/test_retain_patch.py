#!/usr/bin/env python3
"""Exercise resource retention against real files and the production CLI."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import retain_patch


SCRIPT = Path(__file__).with_name("retain_patch.py")
PATCH_BYTES = b"diff --git a/file b/file\n--- a/file\n+++ b/file\n@@ -1,2 +1,2 @@\n-old\n+new\n \n"


class RetainPatchTests(unittest.TestCase):
    def setUp(self):
        scratch = (
            Path(__file__).resolve().parents[2]
            / ".scratchpad"
            / "upgrade-codex-patch"
            / "retention-tests"
        )
        scratch.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.skill = self.root / "upgrade-codex-patch"
        self.skill.mkdir()
        (self.skill / "SKILL.md").write_text("fixture skill\n", encoding="utf-8")
        self.source = self.root / "codex-v0.159.2.patch"
        self.source.write_bytes(PATCH_BYTES)
        self.digest = hashlib.sha256(PATCH_BYTES).hexdigest()
        self.destination = self.skill / "assets" / "patches" / self.source.name

    def retain(self):
        return retain_patch.retain_patch(self.source, self.digest, self.skill)

    def test_retains_exact_bytes_and_preserves_the_source(self):
        result = self.retain()
        self.assertEqual(
            result,
            {
                "schema_version": 1,
                "source": retain_patch.display(self.source),
                "resource": retain_patch.display(self.destination),
                "sha256": self.digest,
                "bytes": len(PATCH_BYTES),
                "outcome": "retained",
                "writes": 1,
            },
        )
        self.assertEqual(self.destination.read_bytes(), PATCH_BYTES)
        self.assertEqual(self.source.read_bytes(), PATCH_BYTES)
        self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])

    def test_identical_resource_is_unchanged(self):
        self.retain()
        before = self.destination.stat()
        result = self.retain()
        self.assertEqual((result["outcome"], result["writes"]), ("unchanged", 0))
        after = self.destination.stat()
        self.assertEqual(
            (after.st_ino, after.st_mtime_ns), (before.st_ino, before.st_mtime_ns)
        )

    def test_git_staging_and_checkout_preserve_patch_bytes(self):
        self.retain()
        attributes = SCRIPT.parent.parent / "assets" / "patches" / ".gitattributes"
        (self.destination.parent / ".gitattributes").write_bytes(
            attributes.read_bytes()
        )
        commands = [
            ["init", "-q"],
            ["config", "core.autocrlf", "true"],
            ["add", "--all"],
            ["diff", "--cached", "--check"],
            [
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "-c",
                "core.hooksPath=",
                "commit",
                "-qm",
                "fixture",
            ],
        ]
        for arguments in commands:
            completed = subprocess.run(
                ["git", "-C", str(self.skill), *arguments],
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
        blob = subprocess.run(
            [
                "git",
                "-C",
                str(self.skill),
                "show",
                "HEAD:assets/patches/" + self.source.name,
            ],
            capture_output=True,
            check=False,
        )
        self.assertEqual(blob.returncode, 0, blob.stderr)
        self.assertEqual(blob.stdout, PATCH_BYTES)
        clone = self.root / "other-machine"
        completed = subprocess.run(
            [
                "git",
                "clone",
                "-q",
                "-c",
                "core.autocrlf=true",
                str(self.skill),
                str(clone),
            ],
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            (clone / "assets" / "patches" / self.source.name).read_bytes(), PATCH_BYTES
        )

    def test_conflicting_resource_is_preserved(self):
        self.destination.parent.mkdir(parents=True)
        self.destination.write_bytes(b"other audited version")
        with self.assertRaises(retain_patch.RetentionError) as raised:
            self.retain()
        self.assertEqual(raised.exception.details["expected"], self.digest)
        self.assertEqual(self.destination.read_bytes(), b"other audited version")
        self.assertEqual(self.source.read_bytes(), PATCH_BYTES)

    def test_source_drift_stops_before_creating_resources(self):
        self.source.write_bytes(PATCH_BYTES + b"unexpected change\n")
        with self.assertRaises(retain_patch.RetentionError) as raised:
            self.retain()
        self.assertEqual(
            raised.exception.details["condition"], "source still matches audited bytes"
        )
        self.assertFalse((self.skill / "assets").exists())

    def test_destination_symlink_does_not_touch_target(self):
        self.destination.parent.mkdir(parents=True)
        try:
            self.destination.symlink_to(self.source)
        except OSError as error:
            self.skipTest(f"symlink fixture unavailable: {error}")
        with self.assertRaises(retain_patch.RetentionError):
            self.retain()
        self.assertTrue(self.destination.is_symlink())
        self.assertEqual(self.source.read_bytes(), PATCH_BYTES)

    def test_resource_directory_cannot_escape_package(self):
        outside = self.root / "outside"
        outside.mkdir()
        try:
            (self.skill / "assets").symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symlink fixture unavailable: {error}")
        with self.assertRaises(retain_patch.RetentionError):
            self.retain()
        self.assertEqual(list(outside.iterdir()), [])

    def test_concurrent_conflicting_publication_is_preserved(self):
        def publish_other(_source, destination):
            Path(destination).write_bytes(b"concurrent patch")
            raise FileExistsError("destination appeared")

        with patch.object(retain_patch.os, "link", side_effect=publish_other):
            with self.assertRaises(retain_patch.RetentionError):
                self.retain()
        self.assertEqual(self.destination.read_bytes(), b"concurrent patch")
        self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])

    def test_cli_reports_retention_and_structured_failure(self):
        arguments = [
            sys.executable,
            "-B",
            str(SCRIPT),
            str(self.source),
            "--sha256",
            self.digest,
            "--skill-root",
            str(self.skill),
        ]
        completed = subprocess.run(
            arguments, capture_output=True, text=True, check=False
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["outcome"], "retained")
        self.assertEqual(completed.stderr, "")
        self.source.write_bytes(b"drift")
        completed = subprocess.run(
            arguments, capture_output=True, text=True, check=False
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(completed.stdout)["expected"], self.digest)
        self.assertEqual(self.destination.read_bytes(), PATCH_BYTES)
        self.source.unlink()
        completed = subprocess.run(
            arguments, capture_output=True, text=True, check=False
        )
        self.assertEqual(completed.returncode, 2)
        failure = json.loads(completed.stdout)
        self.assertEqual(failure["condition"], "resource retention completes")
        self.assertNotIn(str(Path.home()), failure["received"])
        self.assertEqual(self.destination.read_bytes(), PATCH_BYTES)

    def test_invalid_name_and_digest_do_not_write(self):
        with self.assertRaises(retain_patch.RetentionError):
            retain_patch.retain_patch(self.source, "invalid", self.skill)
        other_name = self.root / "patch.diff"
        other_name.write_bytes(PATCH_BYTES)
        with self.assertRaises(retain_patch.RetentionError):
            retain_patch.retain_patch(other_name, self.digest, self.skill)
        self.assertFalse((self.skill / "assets").exists())

    def test_help_and_missing_arguments_do_not_write(self):
        for arguments, status in [(["--help"], 0), ([], 2)]:
            completed = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), *arguments],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, status)
        self.assertFalse((self.skill / "assets").exists())


if __name__ == "__main__":
    unittest.main()
