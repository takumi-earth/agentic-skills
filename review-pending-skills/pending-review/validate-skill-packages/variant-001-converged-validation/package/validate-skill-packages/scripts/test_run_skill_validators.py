#!/usr/bin/env python3
"""Exercise validator outcomes, output fidelity, and progress ordering."""

from __future__ import annotations

import contextlib
import io
import json
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("run_skill_validators.py")
REPO = next(parent for parent in SCRIPT.resolve().parents if (parent / "review-pending-skills").is_dir())


class ValidationDriverTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="validator-test-", dir=REPO / ".scratchpad")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.helper = self.root / "validator.py"

    def validator(self, name: str = "canonical", required: bool = True) -> dict:
        return {
            "id": name, "kind": name, "required": required,
            "command": [str(self.helper), "{package}"], "interpreter": sys.executable,
        }

    def plan(self, validators: list[dict] | None = None, **extra: object) -> dict:
        return {
            "schema_version": 1, "packages": ["skill-a"],
            "validators": validators if validators is not None else [self.validator()],
            "timeout_seconds": 5, **extra,
        }

    def invoke(self, document: object) -> tuple[int, dict, list[dict]]:
        path = self.root / "plan.json"
        path.write_text(json.dumps(document))
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(path)],
            capture_output=True, text=True, check=False, timeout=10,
        )
        events = [json.loads(line) for line in result.stderr.splitlines()]
        return result.returncode, json.loads(result.stdout), events

    def test_process_and_assertion_outcomes_remain_independent(self) -> None:
        for marker, exit_code, expected_code in (("passed", 0, 0), ("passed", 3, 1), ("failed", 0, 1)):
            with self.subTest(marker=marker, exit_code=exit_code):
                self.helper.write_text(f"import sys\nprint('ASSERTIONS: {marker}')\nsys.exit({exit_code})\n")
                code, report, events = self.invoke(self.plan())
                result = report["results"][0]
                self.assertEqual(code, expected_code)
                self.assertEqual(result["inner_assertions"], marker)
                self.assertEqual(result["exit_code"], exit_code)
                self.assertEqual(result["process_passed"], exit_code == 0)
                self.assertEqual(result["check_passed"], expected_code == 0)
                self.assertEqual([event["event"] for event in events], ["validator-starting", "validator-finished"])

    def test_missing_canonical_command_is_not_replaced_by_harness_success(self) -> None:
        self.helper.write_text("print('ok')\n")
        missing = {"id": "canonical", "kind": "canonical", "required": True,
                   "command": ["definitely-missing-validator"]}
        code, report, _ = self.invoke(self.plan([missing, self.validator("harness")]))
        self.assertEqual((code, report["required_failure_count"]), (1, 1))
        self.assertEqual(report["results"][0]["start_state"], "unavailable")
        self.assertEqual(report["results"][1]["exit_code"], 0)

    def test_non_utf8_output_preserves_process_status_and_byte_counts(self) -> None:
        self.helper.write_text("import sys\nsys.stdout.buffer.write(b'partial\\xff')\n")
        code, report, _ = self.invoke(self.plan())
        result = report["results"][0]
        self.assertEqual((code, result["exit_code"]), (0, 0))
        self.assertEqual(result["stdout"], {
            "text": "partial\ufffd", "original_bytes": 8, "emitted_bytes": 8, "omitted_bytes": 0,
        })

    def test_timeout_preserves_partial_binary_output(self) -> None:
        self.helper.write_text(
            "import sys, time\nsys.stdout.buffer.write(b'partial\\xff')\n"
            "sys.stdout.flush()\ntime.sleep(2)\n"
        )
        code, report, _ = self.invoke(self.plan(timeout_seconds=0.2))
        result = report["results"][0]
        self.assertEqual(code, 1)
        self.assertTrue(result["timed_out"])
        self.assertIsNone(result["exit_code"])
        self.assertEqual(result["stdout"]["text"], "partial\ufffd")

    def test_output_bound_does_not_hide_assertion_failure(self) -> None:
        self.helper.write_text("print('x' * 100)\nprint('ASSERTIONS: failed')\n")
        code, report, _ = self.invoke(self.plan(max_output_bytes=10))
        result = report["results"][0]
        self.assertEqual((code, result["inner_assertions"]), (1, "failed"))
        self.assertEqual(result["stdout"]["emitted_bytes"], 10)
        self.assertGreater(result["stdout"]["omitted_bytes"], 0)

    def test_optional_failure_stays_visible_without_failing_required_checks(self) -> None:
        self.helper.write_text("print('ASSERTIONS: failed')\n")
        code, report, _ = self.invoke(self.plan([self.validator("supplemental", required=False)]))
        self.assertEqual(code, 0)
        self.assertFalse(report["results"][0]["check_passed"])
        self.assertEqual(report["required_failure_count"], 0)

    def test_arguments_are_passed_without_shell_interpretation(self) -> None:
        self.helper.write_text("import json, sys\nprint(json.dumps(sys.argv[1:]))\n")
        package = "skill name; $(touch never-create-this)"
        code, report, _ = self.invoke(self.plan(packages=[package]))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(report["results"][0]["stdout"]["text"]), [package])
        self.assertFalse((self.root / "never-create-this").exists())

    def test_relative_working_directory_uses_the_plan_directory(self) -> None:
        (self.root / "work").mkdir()
        self.helper.write_text("from pathlib import Path\nprint(Path.cwd().name)\n")
        code, report, _ = self.invoke(self.plan(working_directory="work"))
        self.assertEqual(code, 0)
        self.assertEqual(report["results"][0]["stdout"]["text"].strip(), "work")

    def test_help_and_invalid_plans_do_not_emit_command_progress(self) -> None:
        help_result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True, check=False,
        )
        self.assertEqual((help_result.returncode, help_result.stderr), (0, ""))
        for document in ([], self.plan(working_directory=False), self.plan(timeout_seconds=float("nan"))):
            with self.subTest(document=document):
                code, report, events = self.invoke(document)
                self.assertEqual(code, 2)
                self.assertTrue(report["errors"])
                self.assertEqual(events, [])

    def test_start_event_precedes_effect_and_uses_one_monotonic_origin(self) -> None:
        namespace = runpy.run_path(str(SCRIPT))
        stream = io.StringIO()

        def child(command: list[str], **kwargs: object) -> subprocess.CompletedProcess:
            event = json.loads(stream.getvalue().splitlines()[-1])
            self.assertEqual((event["event"], event["validator_id"]), ("validator-starting", "canonical"))
            return subprocess.CompletedProcess(command, 0, b"ok\n", b"")

        with contextlib.redirect_stderr(stream), patch.object(
            namespace["time"], "monotonic", side_effect=[0.0, 0.0, 1.0, 2.0, 3.0],
        ), patch.object(namespace["subprocess"], "run", side_effect=child):
            code, report = namespace["run"](self.root / "plan.json", self.plan())
        self.assertEqual(code, 0)
        events = [json.loads(line) for line in stream.getvalue().splitlines()]
        self.assertEqual([event["elapsed_ms"] for event in events], [1000.0, 3000.0])
        self.assertEqual(report["results"][0]["duration_ms"], 2000.0)

    def test_home_paths_are_normalized_in_results_and_progress(self) -> None:
        self.helper.write_text("print('ok')\n")
        code, report, events = self.invoke(self.plan(packages=[str(Path.home() / "skill-fixture")]))
        self.assertEqual(code, 0)
        self.assertEqual(report["results"][0]["package"], "~/skill-fixture")
        self.assertEqual(events[0]["package"], "~/skill-fixture")


if __name__ == "__main__":
    unittest.main()
