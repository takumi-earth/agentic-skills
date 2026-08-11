#!/usr/bin/env python3
"""Direct tests for run_skill_validators.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("run_skill_validators.py")


class ValidationDriverTest(unittest.TestCase):
    def run_plan(
        self,
        root: Path,
        validators: list[dict[str, object]],
        max_output: int = 20000,
        timeout: float = 10,
    ) -> tuple[int, dict[str, object]]:
        plan = {
            "schema_version": 1,
            "packages": ["skill-a"],
            "validators": validators,
            "max_output_bytes": max_output,
            "timeout_seconds": timeout,
            "working_directory": str(root),
        }
        path = root / "plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(path)],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode, json.loads(result.stdout)

    def test_invokes_non_executable_python_helper_through_interpreter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            helper = root / "validator.py"
            helper.write_text("import sys\nprint('ASSERTIONS: passed')\nprint(sys.argv[1])\n", encoding="utf-8")
            code, output = self.run_plan(
                root,
                [
                    {
                        "id": "harness",
                        "kind": "harness",
                        "required": True,
                        "command": [str(helper), "{package}"],
                        "interpreter": sys.executable,
                    }
                ],
            )
        self.assertEqual(code, 0, output)
        result = output["results"][0]
        self.assertEqual(result["inner_assertions"], "passed")
        self.assertEqual(result["exit_code"], 0)
        self.assertTrue(result["process_passed"])

    def test_preserves_assertion_pass_and_nonzero_process_separately(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            helper = root / "validator.py"
            helper.write_text("import sys\nprint('ASSERTIONS: passed')\nsys.exit(3)\n", encoding="utf-8")
            code, output = self.run_plan(
                root,
                [
                    {
                        "id": "canonical",
                        "kind": "canonical",
                        "required": True,
                        "command": [str(helper), "{package}"],
                        "interpreter": sys.executable,
                    }
                ],
            )
        self.assertEqual(code, 1)
        result = output["results"][0]
        self.assertEqual(result["inner_assertions"], "passed")
        self.assertEqual(result["exit_code"], 3)
        self.assertFalse(result["process_passed"])

    def test_missing_canonical_command_is_not_replaced_by_harness_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            helper = root / "harness.py"
            helper.write_text("print('ok')\n", encoding="utf-8")
            code, output = self.run_plan(
                root,
                [
                    {
                        "id": "canonical",
                        "kind": "canonical",
                        "required": True,
                        "command": ["definitely-missing-validator", "{package}"],
                        "interpreter": None,
                    },
                    {
                        "id": "harness",
                        "kind": "harness",
                        "required": True,
                        "command": [str(helper), "{package}"],
                        "interpreter": sys.executable,
                    },
                ],
            )
        self.assertEqual(code, 1)
        self.assertEqual(output["required_failure_count"], 1)
        self.assertEqual(output["results"][0]["start_state"], "unavailable")
        self.assertEqual(output["results"][1]["exit_code"], 0)

    def test_bounds_command_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            helper = root / "validator.py"
            helper.write_text("print('x' * 100)\n", encoding="utf-8")
            code, output = self.run_plan(
                root,
                [
                    {
                        "id": "supplemental",
                        "kind": "supplemental",
                        "required": False,
                        "command": [str(helper), "{package}"],
                        "interpreter": sys.executable,
                    }
                ],
                max_output=10,
            )
        self.assertEqual(code, 0)
        self.assertGreater(output["results"][0]["stdout"]["omitted_bytes"], 0)

    def test_preserves_partial_timeout_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            helper = root / "validator.py"
            helper.write_text(
                "import sys, time\n"
                "sys.stdout.buffer.write(b'partial\\xff')\n"
                "sys.stdout.flush()\n"
                "time.sleep(2)\n",
                encoding="utf-8",
            )
            code, output = self.run_plan(
                root,
                [
                    {
                        "id": "canonical",
                        "kind": "canonical",
                        "required": True,
                        "command": [str(helper), "{package}"],
                        "interpreter": sys.executable,
                    }
                ],
                timeout=0.1,
            )
        self.assertEqual(code, 1)
        result = output["results"][0]
        self.assertTrue(result["timed_out"])
        self.assertIn("partial", result["stdout"]["text"])


if __name__ == "__main__":
    unittest.main()
