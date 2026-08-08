#!/usr/bin/env python3
"""Focused tests for the pending skill inventory."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import pending_skill_inventory


def create_variant(
    root: Path,
    candidate_name: str,
    variant_id: str,
    *,
    metadata_candidate: str | None = None,
) -> Path:
    variant = root / candidate_name / variant_id
    package = variant / "package" / candidate_name
    (package / "agents").mkdir(parents=True)
    (variant / "intent.md").write_text(
        f"# {candidate_name} {variant_id}\n",
        encoding="utf-8",
    )
    (variant / "review.json").write_text(
        json.dumps(
            {
                "activation_effects": ["promotion", "synchronization"],
                "candidate_name": metadata_candidate or candidate_name,
                "predecessors": [],
                "provenance": ["test evidence"],
                "relationships": [{"kind": "overlap", "target": "existing-skill"}],
                "schema_version": 1,
                "status": "pending",
                "variant_id": variant_id,
            }
        ),
        encoding="utf-8",
    )
    (package / "SKILL.md").write_text(
        f"---\nname: {candidate_name}\ndescription: Test candidate.\n---\n",
        encoding="utf-8",
    )
    (package / "agents" / "openai.yaml").write_text(
        "interface:\n  display_name: \"Test\"\n",
        encoding="utf-8",
    )
    return variant


class InventoryTests(unittest.TestCase):
    def test_missing_store_is_an_empty_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "pending-review"

            report = pending_skill_inventory.inventory_pending_store(root)

        self.assertEqual(report["candidate_count"], 0)
        self.assertEqual(report["variant_count"], 0)
        self.assertEqual(report["candidates"], [])

    def test_multiple_variants_are_preserved_and_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "pending-review"
            create_variant(root, "candidate-b", "variant-002")
            create_variant(root, "candidate-a", "variant-002")
            create_variant(root, "candidate-a", "variant-001")

            report = pending_skill_inventory.inventory_pending_store(root)

        self.assertEqual(report["candidate_count"], 2)
        self.assertEqual(report["variant_count"], 3)
        self.assertEqual(
            [candidate["name"] for candidate in report["candidates"]],
            ["candidate-a", "candidate-b"],
        )
        self.assertEqual(
            [
                variant["variant_id"]
                for variant in report["candidates"][0]["variants"]
            ],
            ["variant-001", "variant-002"],
        )
        self.assertNotEqual(
            report["candidates"][0]["variants"][0]["files"]["review"]["sha256"],
            report["candidates"][0]["variants"][1]["files"]["review"]["sha256"],
        )

    def test_missing_required_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "pending-review"
            variant = create_variant(root, "candidate-a", "variant-001")
            (variant / "intent.md").unlink()

            with self.assertRaisesRegex(
                pending_skill_inventory.InventoryError,
                "variant intent is not a regular file",
            ):
                pending_skill_inventory.inventory_pending_store(root)

    def test_metadata_must_match_candidate_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "pending-review"
            create_variant(
                root,
                "candidate-a",
                "variant-001",
                metadata_candidate="different-candidate",
            )

            with self.assertRaisesRegex(
                pending_skill_inventory.InventoryError,
                "candidate_name does not match directory",
            ):
                pending_skill_inventory.inventory_pending_store(root)

    def test_symlinked_variant_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            root = temporary_path / "pending-review"
            candidate = root / "candidate-a"
            candidate.mkdir(parents=True)
            target = temporary_path / "outside"
            target.mkdir()
            (candidate / "variant-001").symlink_to(target, target_is_directory=True)

            with self.assertRaisesRegex(
                pending_skill_inventory.InventoryError,
                "candidate contains a symlink",
            ):
                pending_skill_inventory.inventory_pending_store(root)

    def test_symlinked_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            target = temporary_path / "real-pending-review"
            target.mkdir()
            root = temporary_path / "pending-review"
            root.symlink_to(target, target_is_directory=True)

            with self.assertRaisesRegex(
                pending_skill_inventory.InventoryError,
                "pending-review root is not a real directory",
            ):
                pending_skill_inventory.inventory_pending_store(root)

    def test_symlinked_extra_resource_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            root = temporary_path / "pending-review"
            variant = create_variant(root, "candidate-a", "variant-001")
            target = temporary_path / "outside.txt"
            target.write_text("outside\n", encoding="utf-8")
            (variant / "package" / "candidate-a" / "linked.txt").symlink_to(target)

            with self.assertRaisesRegex(
                pending_skill_inventory.InventoryError,
                "candidate contains a symlink",
            ):
                pending_skill_inventory.inventory_pending_store(root)

    def test_home_paths_render_with_a_tilde_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary) / "home"
            nested = home / "agentic-skills" / "pending-review"

            self.assertEqual(
                pending_skill_inventory.render_path(nested, home),
                "~/agentic-skills/pending-review",
            )


if __name__ == "__main__":
    unittest.main()
