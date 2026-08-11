#!/usr/bin/env python3
"""Direct tests for inventory_transform_debt.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("inventory_transform_debt.py")


class InventoryTransformDebtTest(unittest.TestCase):
    def run_scan(self, repo: Path) -> tuple[int, dict[str, object]]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(repo), "--root", "src"],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode, json.loads(result.stdout)

    def test_emits_stable_signal_only_sites(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            source = repo / "src"
            source.mkdir()
            (source / "patch.rs").write_text(
                'let target = root.join("client/src/api.rs");\n'
                "let contract = ReplaceWholeItemWithContract::new();\n"
                "let id = source_hash(body);\n"
                "let ordinary = semantic_query(owner);\n",
                encoding="utf-8",
            )
            code, first = self.run_scan(repo)
            second_code, second = self.run_scan(repo)
        self.assertEqual(code, 0)
        self.assertEqual(second_code, 0)
        self.assertEqual(first, second)
        sites = first["sites"]
        self.assertEqual(len(sites), 3)
        self.assertTrue(all(site["review_state"] == "signal-only" for site in sites))
        self.assertTrue(all(site["disposition"] == "review" for site in sites))
        self.assertNotIn("ordinary", json.dumps(first))

    def test_rejects_root_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            outside = Path(directory) / "outside.rs"
            outside.write_text("source.replace(old, new)\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--repo", str(repo), "--root", str(outside)],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("escapes repository", result.stdout)


if __name__ == "__main__":
    unittest.main()
