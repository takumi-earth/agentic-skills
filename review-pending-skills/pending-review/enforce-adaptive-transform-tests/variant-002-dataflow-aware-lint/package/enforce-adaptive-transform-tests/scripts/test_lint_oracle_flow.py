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
            "    output = 'usage: tool'\n"
            "    assert output == 'usage: tool'\n\n"
            "@exact_output_contract\n"
            "def test_generated_source():\n"
            "    output = render_source()\n"
            "    assert output == 'owned bytes'\n"
        )
        self.assertEqual(code, 0, output)
        self.assertEqual(output["finding_count"], 0)


    def test_keyword_helpers_and_returned_source(self):
        for code in (
            "def passthrough(value):\n    return value\ndef test_one():\n    assert passthrough(value=render_source()) == 'x'\n",
            "def check(value):\n    assert value == 'x'\ndef test_one():\n    check(value=render_source())\n",
            "def output():\n    return syntax_text(parse_source('x'))\ndef test_one():\n    assert output() == 'x'\n",
        ):
            with self.subTest(code=code):
                status, output = self.run_lint(code)
                self.assertEqual(status, 1, output)
                self.assertTrue(output['reports'][0]['findings'])

    def test_reassignment_and_typed_cardinality(self):
        status, output = self.run_lint("def test_one():\n    text = render_source()\n    text = 'ordinary'\n    assert text == 'ordinary'\n    nodes = parse_source('x').functions()\n    assert len(nodes) == 1\n")
        self.assertEqual(status, 0, output)
        self.assertEqual(output['finding_count'], 0)

    def test_unknown_is_not_clean(self):
        for code in (
            "def test_one():\n    assert imported_helper(render_source()) == 'x'\n",
            "def test_one():\n    text = render_source()\n    if condition():\n        text = 'ordinary'\n    assert text == 'x'\n",
            "def test_one():\n    value = [render_source()][0]\n    assert value == 'x'\n",
        ):
            status, output = self.run_lint(code)
            self.assertEqual(status, 3, output)
            self.assertEqual(output['status'], 'unknown')
            self.assertTrue(output['reports'][0]['unknown'])

    def test_exemption_does_not_leak_to_nested_or_called_functions(self):
        status, output = self.run_lint("@exact_output_contract\ndef test_outer():\n    def nested():\n        assert render_source() == 'x'\n    assert render_source() == 'owned'\n    nested()\n")
        self.assertEqual(status, 1, output)
        self.assertEqual({f['line'] for f in output['reports'][0]['findings']}, {4})

    def test_nonassertion_guard_is_not_a_text_oracle(self):
        status, output = self.run_lint("def test_one():\n    matches = render_source().startswith('prefix')\n")
        self.assertEqual(output['finding_count'], 0)
        self.assertEqual(status, 0, output)


if __name__ == "__main__":
    unittest.main()
