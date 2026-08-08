#!/usr/bin/env python3
"""Focused tests for immutable script variant creation."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
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
                (first / "experiment.py").read_text(),
                "print('first')\n",
            )
            self.assertEqual(
                (second / "experiment.py").read_text(),
                "print('second')\n",
            )
            self.assertEqual(first_manifest["predecessors"], [])
            self.assertEqual(
                second_manifest["predecessors"],
                ["variant-001-first"],
            )
            self.assertNotEqual(
                first_manifest["source_sha256"],
                second_manifest["source_sha256"],
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
            self.assertEqual((target / "experiment.py").read_text(), "original\n")

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


if __name__ == "__main__":
    unittest.main()
