#!/usr/bin/env python3

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("compare_patch_hunks.py")
SPEC = importlib.util.spec_from_file_location("compare_patch_hunks", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot import {SCRIPT}")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def patch_for(path: str, hunk_header: str, removed: str, added: str) -> str:
    return f"""\
diff --git a/{path} b/{path}
index 1111111..2222222 100644
--- a/{path}
+++ b/{path}
{hunk_header}
 context before
-{removed}
+{added}
 context after
"""


class ComparePatchHunksTests(unittest.TestCase):
    def write_patch(self, directory: Path, name: str, content: str) -> Path:
        path = directory / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_ignores_hunk_offsets_context_and_index_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            old_path = self.write_patch(
                directory,
                "old.patch",
                patch_for("src/lib.rs", "@@ -2,3 +2,3 @@", "old()", "new()"),
            )
            new_patch = patch_for(
                "src/lib.rs", "@@ -92,3 +108,3 @@", "old()", "new()"
            ).replace("context before", "different unchanged context")
            new_path = self.write_patch(directory, "new.patch", new_patch)

            comparison = MODULE.compare_patches(
                MODULE.parse_patch(old_path), MODULE.parse_patch(new_path)
            )

            self.assertTrue(comparison.is_identical)
            self.assertEqual(comparison.common[0].exact_hunks, 1)

    def test_reports_changed_edit_stream_and_preserves_exact_sibling_hunk(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            shared = patch_for(
                "src/lib.rs", "@@ -2,3 +2,3 @@", "before()", "after()"
            )
            old_path = self.write_patch(
                directory,
                "old.patch",
                shared
                + patch_for(
                    "src/main.rs", "@@ -4,3 +4,3 @@", "single_line()", "wrapped()"
                ),
            )
            new_path = self.write_patch(
                directory,
                "new.patch",
                shared
                + patch_for(
                    "src/main.rs",
                    "@@ -4,3 +4,4 @@",
                    "single_line()",
                    "wrapped(\n+    value)",
                ),
            )

            comparison = MODULE.compare_patches(
                MODULE.parse_patch(old_path), MODULE.parse_patch(new_path)
            )

            self.assertFalse(comparison.is_identical)
            self.assertEqual(
                tuple(item.path for item in comparison.differing), ("src/main.rs",)
            )
            lib = next(item for item in comparison.common if item.path == "src/lib.rs")
            self.assertEqual(lib.exact_hunks, 1)

    def test_reports_new_and_removed_file_sections(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            old_path = self.write_patch(
                directory,
                "old.patch",
                patch_for("src/old.rs", "@@ -1,3 +1,3 @@", "old", "new"),
            )
            new_path = self.write_patch(
                directory,
                "new.patch",
                patch_for("src/new.rs", "@@ -1,3 +1,3 @@", "old", "new"),
            )

            comparison = MODULE.compare_patches(
                MODULE.parse_patch(old_path), MODULE.parse_patch(new_path)
            )

            self.assertEqual(comparison.old_only, ("src/old.rs",))
            self.assertEqual(comparison.new_only, ("src/new.rs",))
            self.assertFalse(comparison.is_identical)

    def test_preserves_edits_that_resemble_file_headers(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            path = self.write_patch(
                directory,
                "markers.patch",
                patch_for(
                    "src/lib.rs",
                    "@@ -1,3 +1,3 @@",
                    "-- removed marker",
                    "++ added marker",
                ),
            )

            parsed = MODULE.parse_patch(path)

            self.assertEqual(
                parsed["src/lib.rs"].edit_stream,
                ("--- removed marker", "+++ added marker"),
            )

    def test_require_identical_exit_status_distinguishes_changes(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            old_path = self.write_patch(
                directory,
                "old.patch",
                patch_for("src/lib.rs", "@@ -1,3 +1,3 @@", "old", "new"),
            )
            same_path = self.write_patch(
                directory,
                "same.patch",
                patch_for("src/lib.rs", "@@ -8,3 +8,3 @@", "old", "new"),
            )
            changed_path = self.write_patch(
                directory,
                "changed.patch",
                patch_for("src/lib.rs", "@@ -8,3 +8,3 @@", "old", "different"),
            )

            same = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--require-identical",
                    str(old_path),
                    str(same_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            changed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--require-identical",
                    str(old_path),
                    str(changed_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(same.returncode, 0, same.stderr)
            self.assertEqual(changed.returncode, 1, changed.stderr)
            self.assertIn("DIFFERS src/lib.rs", changed.stdout)

    def test_rejects_patch_without_git_diff_sections(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            path = self.write_patch(Path(raw_directory), "bad.patch", "not a patch\n")

            with self.assertRaisesRegex(MODULE.PatchParseError, "no `diff --git`"):
                MODULE.parse_patch(path)


if __name__ == "__main__":
    unittest.main()
