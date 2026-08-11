#!/usr/bin/env python3
"""Focused tests for immutable script variant creation."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

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
