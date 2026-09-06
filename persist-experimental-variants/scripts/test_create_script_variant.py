#!/usr/bin/env python3
"""Focused tests for immutable script variant creation."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
import ctypes
import errno
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import create_script_variant


class CreateVariantTests(unittest.TestCase):
    def test_distinct_variants_preserve_bytes_and_intent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "experiment.py"
            source.write_text("print('first')\n", encoding="utf-8")

            first = create_script_variant.create_variant(
                source=source,
                notebook_root=root / "notebook",
                variant_id="variant-001-first",
                intent="Try the first concrete approach",
                predecessors=[],
            )
            source.write_text("print('second')\n", encoding="utf-8")
            second = create_script_variant.create_variant(
                source=source,
                notebook_root=root / "notebook",
                variant_id="variant-002-second",
                intent="Try a second approach without replacing the first",
                predecessors=["variant-001-first"],
            )

            first_manifest = json.loads((first / "variant.json").read_text())
            second_manifest = json.loads((second / "variant.json").read_text())
            self.assertEqual(
                (first / "artifact" / "experiment.py").read_text(),
                "print('first')\n",
            )
            self.assertEqual(
                (second / "artifact" / "experiment.py").read_text(),
                "print('second')\n",
            )
            self.assertEqual(first_manifest["schema_version"], 2)
            self.assertEqual(first_manifest["payload_path"], "artifact/experiment.py")
            self.assertEqual(first_manifest["predecessors"], [])
            self.assertEqual(
                second_manifest["predecessors"],
                ["variant-001-first"],
            )
            self.assertNotEqual(
                first_manifest["payload_sha256"],
                second_manifest["payload_sha256"],
            )

    def test_existing_variant_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "experiment.py"
            source.write_text("original\n", encoding="utf-8")
            target = create_script_variant.create_variant(
                source=source,
                notebook_root=root / "notebook",
                variant_id="variant-001",
                intent="Original intent",
                predecessors=[],
            )
            source.write_text("replacement\n", encoding="utf-8")

            with self.assertRaisesRegex(
                create_script_variant.VariantError,
                "will not be overwritten",
            ):
                create_script_variant.create_variant(
                    source=source,
                    notebook_root=root / "notebook",
                    variant_id="variant-001",
                    intent="Replacement intent",
                    predecessors=[],
                )
            self.assertEqual(
                (target / "artifact" / "experiment.py").read_text(),
                "original\n",
            )

    def test_symlink_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            actual = root / "actual.py"
            actual.write_text("content\n", encoding="utf-8")
            source = root / "source.py"
            source.symlink_to(actual)

            with self.assertRaisesRegex(
                create_script_variant.VariantError,
                "regular non-symlink file",
            ):
                create_script_variant.create_variant(
                    source=source,
                    notebook_root=root / "notebook",
                    variant_id="variant-001",
                    intent="Do not follow symlink sources",
                    predecessors=[],
                )

    def test_metadata_named_sources_are_kept_beneath_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index, source_name in enumerate(("intent.md", "variant.json"), start=1):
                with self.subTest(source_name=source_name):
                    source_root = root / f"source-{index}"
                    source_root.mkdir()
                    source = source_root / source_name
                    source.write_text(f"payload for {source_name}\n", encoding="utf-8")
                    target = create_script_variant.create_variant(
                        source=source,
                        notebook_root=root / f"notebook-{index}",
                        variant_id="variant-001",
                        intent=f"Preserve a source named {source_name}",
                        predecessors=[],
                    )

                    manifest = json.loads((target / "variant.json").read_text())
                    self.assertEqual(
                        (target / "artifact" / source_name).read_text(),
                        f"payload for {source_name}\n",
                    )
                    self.assertEqual(manifest["payload_path"], f"artifact/{source_name}")
                    self.assertEqual(
                        manifest["payload_sha256"],
                        create_script_variant.sha256_file(target / "artifact" / source_name),
                    )
                    self.assertIn("Preserve a source named", (target / "intent.md").read_text())

    def test_invalid_predecessor_relationships_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            notebook = root / "notebook"
            source = root / "experiment.py"
            source.write_text("payload\n", encoding="utf-8")

            cases = [
                ("predecessor-self", ["variant-002"]),
                ("predecessor-duplicate", ["variant-001", "variant-001"]),
                ("predecessor-missing", ["variant-404"]),
            ]
            create_script_variant.create_variant(
                source=source,
                notebook_root=notebook,
                variant_id="variant-001",
                intent="Valid predecessor",
                predecessors=[],
            )
            for code, predecessors in cases:
                with self.subTest(code=code):
                    with self.assertRaises(create_script_variant.VariantError) as raised:
                        create_script_variant.create_variant(
                            source=source,
                            notebook_root=notebook,
                            variant_id="variant-002",
                            intent="Invalid relationship",
                            predecessors=predecessors,
                        )
                    self.assertEqual(raised.exception.code, code)

    def test_malformed_and_identity_mismatched_predecessors_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "experiment.py"
            source.write_text("payload\n", encoding="utf-8")

            malformed_notebook = root / "malformed-notebook"
            malformed = malformed_notebook / "variant-001"
            malformed.mkdir(parents=True)
            (malformed / "intent.md").write_text("Intent\n", encoding="utf-8")
            (malformed / "variant.json").write_text("not JSON\n", encoding="utf-8")
            with self.assertRaises(create_script_variant.VariantError) as malformed_error:
                create_script_variant.create_variant(
                    source=source,
                    notebook_root=malformed_notebook,
                    variant_id="variant-002",
                    intent="Reject malformed predecessor",
                    predecessors=["variant-001"],
                )
            self.assertEqual(malformed_error.exception.code, "predecessor-malformed")

            mismatch_notebook = root / "mismatch-notebook"
            predecessor = create_script_variant.create_variant(
                source=source,
                notebook_root=mismatch_notebook,
                variant_id="variant-001",
                intent="Create identity fixture",
                predecessors=[],
            )
            manifest_path = predecessor / "variant.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["variant_id"] = "variant-other"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(create_script_variant.VariantError) as mismatch_error:
                create_script_variant.create_variant(
                    source=source,
                    notebook_root=mismatch_notebook,
                    variant_id="variant-002",
                    intent="Reject identity mismatch",
                    predecessors=["variant-001"],
                )
            self.assertEqual(
                mismatch_error.exception.code,
                "predecessor-identity-mismatch",
            )

    def test_preexisting_empty_target_is_never_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "experiment.py"
            source.write_text("payload\n", encoding="utf-8")
            notebook = root / "notebook"
            target = notebook / "variant-001"
            target.mkdir(parents=True)

            with self.assertRaises(create_script_variant.VariantError) as raised:
                create_script_variant.create_variant(
                    source=source,
                    notebook_root=notebook,
                    variant_id="variant-001",
                    intent="Do not replace an empty target",
                    predecessors=[],
                )
            self.assertEqual(raised.exception.code, "variant-exists")
            self.assertEqual(list(target.iterdir()), [])

    def test_concurrent_creators_produce_exactly_one_variant(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            notebook = root / "notebook"
            sources: list[Path] = []
            for index in range(2):
                source_root = root / f"source-{index}"
                source_root.mkdir()
                source = source_root / "experiment.py"
                source.write_bytes((f"payload-{index}\n" * 200_000).encode())
                sources.append(source)
            barrier = threading.Barrier(2)

            def create(source: Path) -> tuple[str, str]:
                barrier.wait()
                try:
                    target = create_script_variant.create_variant(
                        source=source,
                        notebook_root=notebook,
                        variant_id="variant-001",
                        intent=f"Concurrent source {source.parent.name}",
                        predecessors=[],
                    )
                except create_script_variant.VariantError as error:
                    return "error", error.code
                return "created", str(target)

            with ThreadPoolExecutor(max_workers=2) as executor:
                outcomes = list(executor.map(create, sources))

            self.assertEqual([kind for kind, _ in outcomes].count("created"), 1)
            self.assertEqual([kind for kind, _ in outcomes].count("error"), 1)
            error_code = next(value for kind, value in outcomes if kind == "error")
            self.assertIn(error_code, {"variant-claimed", "variant-exists"})
            target = notebook / "variant-001"
            manifest = json.loads((target / "variant.json").read_text())
            payload = target / manifest["payload_path"]
            self.assertIn(payload.read_bytes(), {source.read_bytes() for source in sources})
            self.assertEqual(
                manifest["payload_sha256"],
                create_script_variant.sha256_file(payload),
            )
            self.assertFalse((notebook / ".variant-001.claim").exists())

    def test_targets_created_during_copy_are_preserved(self) -> None:
        for kind in ("empty-directory", "nonempty-directory", "file", "symlink"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = root / "experiment.py"
                source.write_bytes(b"original payload\n")
                notebook = root / "notebook"
                target = notebook / "variant-001"
                other_file = root / "other.txt"
                other_file.write_bytes(b"unrelated bytes\n")
                copy_file = create_script_variant.shutil.copyfile
                inserted_identity = []

                def copy_then_create_target(src: Path, dst: Path) -> Path:
                    result = copy_file(src, dst)
                    if kind.endswith("directory"):
                        target.mkdir()
                        if kind == "nonempty-directory":
                            (target / "other.txt").write_bytes(b"unrelated bytes\n")
                    elif kind == "file":
                        target.write_bytes(b"unrelated bytes\n")
                    else:
                        target.symlink_to(other_file)
                    inserted_identity.append(target.lstat())
                    return result

                with patch.object(
                    create_script_variant.shutil, "copyfile", copy_then_create_target
                ):
                    with self.assertRaises(create_script_variant.VariantError) as raised:
                        create_script_variant.create_variant(
                            source=source,
                            notebook_root=notebook,
                            variant_id="variant-001",
                            intent="Preserve a destination created by another writer",
                            predecessors=[],
                        )

                self.assertEqual(raised.exception.code, "variant-exists")
                self.assertEqual(target.lstat().st_ino, inserted_identity[0].st_ino)
                self.assertEqual(target.lstat().st_dev, inserted_identity[0].st_dev)
                self.assertEqual(set(notebook.iterdir()), {target})
                if kind == "empty-directory":
                    self.assertEqual(list(target.iterdir()), [])
                elif kind == "nonempty-directory":
                    self.assertEqual(
                        (target / "other.txt").read_bytes(), b"unrelated bytes\n"
                    )
                else:
                    self.assertEqual(target.read_bytes(), b"unrelated bytes\n")
                self.assertEqual(other_file.read_bytes(), b"unrelated bytes\n")
                self.assertEqual(source.read_bytes(), b"original payload\n")

    def test_native_adapters_preserve_conflict_errors(self) -> None:
        source = Path("prepared")
        target = Path("target")
        for platform, symbol, arguments in (
            ("linux", "renameat2", (-100, b"prepared", -100, b"target", 1)),
            ("darwin", "renamex_np", (b"prepared", b"target", 4)),
        ):
            with self.subTest(platform=platform):
                def conflict(*args: object) -> int:
                    ctypes.set_errno(errno.EEXIST)
                    return -1

                rename = Mock(side_effect=conflict)
                library = SimpleNamespace(**{symbol: rename})
                with patch.object(create_script_variant.sys, "platform", platform), patch.object(
                    create_script_variant.ctypes, "CDLL", return_value=library
                ):
                    with self.assertRaises(FileExistsError) as raised:
                        create_script_variant.publish_without_replacement(source, target)
                rename.assert_called_once_with(*arguments)
                self.assertEqual(raised.exception.filename, str(source))
                self.assertEqual(raised.exception.filename2, str(target))

        with patch.object(create_script_variant.sys, "platform", "win32"), patch.object(
            Path, "rename", side_effect=FileExistsError(errno.EEXIST, "target exists")
        ):
            with self.assertRaises(FileExistsError):
                create_script_variant.publish_without_replacement(source, target)

    def test_unavailable_publication_does_not_fall_back_to_replacement(self) -> None:
        for platform in ("linux", "unsupported-platform"):
            with self.subTest(platform=platform), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = root / "experiment.py"
                source.write_bytes(b"payload\n")
                notebook = root / "notebook"
                with patch.object(create_script_variant.sys, "platform", platform), patch.object(
                    create_script_variant.ctypes, "CDLL", return_value=SimpleNamespace()
                ):
                    with self.assertRaises(create_script_variant.VariantError) as raised:
                        create_script_variant.create_variant(
                            source=source,
                            notebook_root=notebook,
                            variant_id="variant-001",
                            intent="Require non-replacing publication",
                            predecessors=[],
                        )
                self.assertEqual(raised.exception.code, "filesystem-failure")
                self.assertEqual(list(notebook.iterdir()), [])
                self.assertEqual(source.read_bytes(), b"payload\n")

    def test_copy_failure_keeps_cli_status_and_normalizes_error_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "experiment.py"
            source.write_bytes(b"payload\n")
            notebook = root / "notebook"
            error_source = Path.home() / "input files" / "experiment.py"
            error_target = Path.home() / "output files" / "experiment.py"
            failure = OSError(
                errno.EIO, "Injected copy failure", str(error_source), None, str(error_target)
            )
            arguments = [
                "create_script_variant.py", "--source", str(source),
                "--notebook-root", str(notebook), "--external-deliverable",
                "--variant-id", "variant-001", "--intent", "Report a copy failure",
            ]
            output = io.StringIO()
            with patch.object(sys, "argv", arguments), patch.object(
                create_script_variant.shutil, "copyfile", side_effect=failure
            ), redirect_stdout(output):
                status = create_script_variant.main()

            self.assertEqual(status, 3)
            self.assertTrue(
                output.getvalue().startswith("VARIANT_ERROR[filesystem-failure]:")
            )
            self.assertIn("~/input files/experiment.py", output.getvalue())
            self.assertIn("~/output files/experiment.py", output.getvalue())
            self.assertNotIn(str(Path.home()), output.getvalue())
            self.assertEqual(list(notebook.iterdir()), [])
            self.assertEqual(source.read_bytes(), b"payload\n")

    def test_diagnostic_normalization_preserves_neighboring_home_names(self) -> None:
        home = Path.home()
        neighbor = home.with_name(home.name + "-neighbor") / "file.txt"
        error = OSError(
            errno.EIO, "Failure", str(neighbor), None, str(home / "file.txt")
        )
        diagnostic = create_script_variant.render_operational_error(error)
        self.assertIn(repr(str(neighbor)), diagnostic)
        self.assertIn("~/file.txt", diagnostic)

    def test_payload_home_paths_remain_exact_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "experiment.py"
            payload = b"source path: " + os.fsencode(Path.home()) + b"\n\x00\xff"
            source.write_bytes(payload)
            target = create_script_variant.create_variant(
                source=source,
                notebook_root=root / "notebook",
                variant_id="variant-001",
                intent="Normalize diagnostics without rewriting payload bytes",
                predecessors=[],
            )
            self.assertEqual((target / "artifact" / "experiment.py").read_bytes(), payload)

    def test_canonical_default_and_external_destination_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "agentic-skills"
            (repository / ".git").mkdir(parents=True)
            (repository / "AGENTS.md").write_text("# fixture\n", encoding="utf-8")
            review = repository / "review-pending-skills"
            review.mkdir()
            (review / "SKILL.md").write_text("---\nname: fixture\n---\n", encoding="utf-8")
            script = repository / "nested" / "scripts" / "helper.py"

            resolved = create_script_variant.resolve_canonical_repository(script)
            selected = create_script_variant.select_notebook_root(
                repository=resolved,
                notebook_id="sqlite-approaches",
                notebook_root=None,
                external_deliverable=False,
            )
            self.assertEqual(
                selected,
                repository
                / ".scratchpad"
                / "persist-experimental-variants"
                / "sqlite-approaches",
            )

            external = root / "deliverable"
            with self.assertRaises(create_script_variant.VariantError) as unauthorized:
                create_script_variant.select_notebook_root(
                    repository=resolved,
                    notebook_id=None,
                    notebook_root=external,
                    external_deliverable=False,
                )
            self.assertEqual(
                unauthorized.exception.code,
                "external-destination-unauthorized",
            )
            self.assertEqual(
                create_script_variant.select_notebook_root(
                    repository=resolved,
                    notebook_id=None,
                    notebook_root=external,
                    external_deliverable=True,
                ),
                external,
            )

    def test_cli_reports_stable_error_and_distinct_status(self) -> None:
        missing = Path.home() / f".missing-variant-source-{id(self)}"
        completed = subprocess.run(
            [
                sys.executable,
                str(Path(create_script_variant.__file__)),
                "--source",
                str(missing),
                "--notebook-id",
                "error-fixture",
                "--variant-id",
                "variant-001",
                "--intent",
                "Exercise stable failures",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, create_script_variant.VARIANT_ERROR_EXIT)
        self.assertTrue(completed.stdout.startswith("VARIANT_ERROR[source-invalid]:"))
        self.assertIn("~/.missing-variant-source-", completed.stdout)
        self.assertNotIn(str(Path.home().resolve()), completed.stdout)
        self.assertEqual(completed.stderr, "")

    def test_cli_converts_notebook_filesystem_shape_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "experiment.py"
            source.write_text("payload\n", encoding="utf-8")
            notebook = root / "notebook-file"
            notebook.write_text("not a directory\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(Path(create_script_variant.__file__)),
                    "--source",
                    str(source),
                    "--notebook-root",
                    str(notebook),
                    "--external-deliverable",
                    "--variant-id",
                    "variant-001",
                    "--intent",
                    "Exercise a filesystem shape failure",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, create_script_variant.VARIANT_ERROR_EXIT)
            self.assertTrue(
                completed.stdout.startswith("VARIANT_ERROR[notebook-root-invalid]:")
            )
            self.assertEqual(completed.stderr, "")
            self.assertEqual(notebook.read_text(), "not a directory\n")

    def test_cli_external_deliverable_prints_one_human_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "experiment.py"
            source.write_text("payload\n", encoding="utf-8")
            notebook = root / "deliverable-notebook"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(Path(create_script_variant.__file__)),
                    "--source",
                    str(source),
                    "--notebook-root",
                    str(notebook),
                    "--external-deliverable",
                    "--variant-id",
                    "variant-001",
                    "--intent",
                    "Exercise external deliverable output",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            target = notebook / "variant-001"
            self.assertEqual(completed.returncode, 0, completed.stdout)
            self.assertEqual(completed.stdout, f"{create_script_variant.render_path(target)}\n")
            self.assertEqual(completed.stderr, "")
            self.assertEqual((target / "artifact" / "experiment.py").read_text(), "payload\n")

    def test_home_paths_render_with_a_tilde_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "home"
            nested = home / "notebooks" / "variant-001"

            self.assertEqual(
                create_script_variant.render_path(nested, home),
                "~/notebooks/variant-001",
            )


if __name__ == "__main__":
    unittest.main()
