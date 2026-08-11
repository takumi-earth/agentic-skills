#!/usr/bin/env python3
"""Direct tests for lint_oracle_flow.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("lint_oracle_flow.py")


class OracleFlowTest(unittest.TestCase):
    def run_lint(self, source: str) -> tuple[int, dict[str, object]]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test_case.py"
            path.write_text(source, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
        return result.returncode, json.loads(result.stdout)

    def test_flags_parse_then_text_and_custom_wrapper(self) -> None:
        code, output = self.run_lint(
            "def passthrough(value):\n"
            "    return value\n\n"
            "def test_transform():\n"
            "    text = syntax_text(parse_source('fn f() {}'))\n"
            "    wrapped = passthrough(text)\n"
            "    assert wrapped.startswith('fn f')\n"
            "    assert 'target' in text\n"
        )
        self.assertEqual(code, 1)
        rules = {finding["rule"] for finding in output["reports"][0]["findings"]}
        self.assertIn("method-startswith", rules)
        self.assertIn("membership", rules)

    def test_flags_regex_snapshot_and_raw_equality(self) -> None:
        code, output = self.run_lint(
            "import re\n\n"
            "def test_transform():\n"
            "    value = render_source()\n"
            "    assert re.search('needle', value)\n"
            "    assert value == 'full source'\n"
            "    assert_snapshot(value)\n"
        )
        self.assertEqual(code, 1)
        rules = {finding["rule"] for finding in output["reports"][0]["findings"]}
        self.assertTrue({"regex", "raw-equality", "snapshot"}.issubset(rules))

    def test_allows_legitimate_strings_and_explicit_exact_output(self) -> None:
        code, output = self.run_lint(
            "def test_cli_output():\n"
            "    output = run_cli()\n"
            "    assert output == 'usage: tool'\n\n"
            "@exact_output_contract\n"
            "def test_generated_source():\n"
            "    output = render_source()\n"
            "    assert output == 'owned bytes'\n"
        )
        self.assertEqual(code, 0, output)
        self.assertEqual(output["finding_count"], 0)


if __name__ == "__main__":
    unittest.main()
