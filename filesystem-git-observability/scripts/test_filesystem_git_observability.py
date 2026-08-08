#!/usr/bin/env python3
"""Direct behavior tests for every packaged observability script."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIRECTORY))

from investigate_git_config_metadata import InvestigationError  # noqa: E402
from investigate_git_config_metadata import one_mode_experiment  # noqa: E402
from investigate_git_config_metadata import resolve_scratchpad_root  # noqa: E402


class ObservabilityScriptTests(unittest.TestCase):
    """Exercise success and failure polarity through packaged entry points."""

    scratchpad_root: Path

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="filesystem-git-observability-tests-",
            dir=self.scratchpad_root,
        )
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_script(
        self, name: str, *arguments: str, expected_exit: int = 0
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_DIRECTORY / name), *arguments],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            expected_exit,
            msg=(
                f"script exit check failed; script={name}; expected={expected_exit}; "
                f"received={completed.returncode}; stdout={completed.stdout!r}; "
                f"stderr={completed.stderr!r}"
            ),
        )
        return completed

    def test_inspect_source_supports_lines_and_exact_mismatch_diagnostics(self) -> None:
        source = self.root / "source.txt"
        source.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
        context_output = self.root / "reports" / "selected-context.txt"

        self.run_script(
            "inspect_source_context.py",
            "--source",
            str(source),
            "--output",
            str(context_output),
            "--line",
            "2",
            "--context",
            "0",
        )
        selected_context = context_output.read_text(encoding="utf-8")
        self.assertIn("selected_lines=2", selected_context)
        self.assertIn("00002: beta", selected_context)

        mismatch = self.run_script(
            "inspect_source_context.py",
            "--source",
            str(source),
            "--output",
            str(self.root / "reports" / "missing-context.txt"),
            "--needle",
            "missing",
            "--expected-matches",
            "1",
            expected_exit=1,
        )
        self.assertIn("condition=line contains marker", mismatch.stderr)
        self.assertIn("expected=1", mismatch.stderr)
        self.assertIn("received=0", mismatch.stderr)

    def test_persist_command_report_captures_exact_argv_and_input_hash(self) -> None:
        source = self.root / "input.txt"
        source.write_text("auditable input\n", encoding="utf-8")
        emitter = self.root / "emit_json.py"
        emitter.write_text(
            "#!/usr/bin/env python3\n"
            "import json\n"
            "print(json.dumps({'status': 'ok', 'value': 7}))\n",
            encoding="utf-8",
        )
        output = self.root / "reports" / "command.json"

        completed = self.run_script(
            "persist_command_report.py",
            "--output",
            str(output),
            "--purpose",
            "test-command-capture",
            "--input",
            str(source),
            "--parse-json",
            "--",
            sys.executable,
            str(emitter),
        )
        summary = json.loads(completed.stdout)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(summary["exit_code"], 0)
        self.assertEqual(report["command"], [sys.executable, str(emitter)])
        self.assertEqual(report["report"], {"status": "ok", "value": 7})
        self.assertEqual(
            report["input_sha256_before"][str(source)],
            hashlib.sha256(source.read_bytes()).hexdigest(),
        )
        self.assertEqual(report["input_sha256_after"], report["input_sha256_before"])
        self.assertTrue(Path(report["write_ahead_artifact"]).is_file())

    def test_search_evidence_applies_match_cap_per_marker(self) -> None:
        evidence_root = self.root / "evidence"
        evidence_root.mkdir()
        source = evidence_root / "trace.log"
        source.write_text(
            " ".join(["FIRST"] * 101 + ["SECOND"] * 101),
            encoding="utf-8",
        )
        output = self.root / "reports" / "search.json"

        self.run_script(
            "search_execution_evidence.py",
            "--root",
            str(evidence_root),
            "--marker",
            "first=FIRST",
            "--marker",
            "second=SECOND",
            "--output",
            str(output),
        )
        report = json.loads(output.read_text(encoding="utf-8"))
        finding = report["matching_files"][0]
        self.assertEqual(finding["marker_counts"], {"first": 100, "second": 100})
        self.assertEqual(finding["truncated_markers"], ["first", "second"])

    def test_analyze_rollout_distinguishes_runtime_and_internal_markers(self) -> None:
        digest = "a" * 64
        rollout = self.root / "rollout.jsonl"
        records = [
            {
                "timestamp": "2026-08-08T00:00:00Z",
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "output": f"RUN_MARKER INTERNAL_STATE {digest}",
                },
            },
            {
                "timestamp": "2026-08-08T00:00:01Z",
                "type": "event_msg",
                "payload": {"type": "message", "text": "RUN_MARKER"},
            },
        ]
        rollout.write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )
        output = self.root / "reports" / "rollout.json"

        self.run_script(
            "analyze_rollout_evidence.py",
            "--rollout",
            str(rollout),
            "--output",
            str(output),
            "--marker",
            "runtime=RUN_MARKER",
            "--marker",
            "internal=INTERNAL_STATE",
            "--internal-marker",
            "internal",
        )
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["bounded_runtime_marker_counts"], {"internal": 1, "runtime": 1})
        self.assertEqual(report["bounded_runtime_sha256_tokens"], [digest])
        self.assertEqual(report["serialized_internal_state_markers"], ["internal"])

    def test_metadata_experiment_observes_without_creating_a_gate(self) -> None:
        fixture_root = self.root / "metadata-fixtures"
        fixture_root.mkdir()

        report = one_mode_experiment(
            fixture_root,
            number=1,
            mode=0o664,
            parent_mode=0o755,
            desired_gid=None,
            target_value="https://example.invalid/repository.git",
        )

        self.assertEqual(report["exit_code"], 0)
        self.assertTrue(report["command_check"]["passed"])
        self.assertFalse(report["metadata_acceptance_gate"])
        for change in report["observed_metadata_changes"].values():
            self.assertEqual(set(change), {"before", "after"})

    def test_metadata_fixture_root_rejects_non_scratchpad_path_explicitly(self) -> None:
        received = Path("/non-scratch-observability-fixture")

        with self.assertRaises(InvestigationError) as caught:
            resolve_scratchpad_root(received)

        message = str(caught.exception)
        self.assertIn("condition=fixture root is beneath", message)
        self.assertIn("expected=path containing '.scratchpad'", message)
        self.assertIn(f"received={received}", message)


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scratchpad-root", type=Path, required=True)
    return parser.parse_known_args()


if __name__ == "__main__":
    arguments, unittest_arguments = parse_args()
    ObservabilityScriptTests.scratchpad_root = resolve_scratchpad_root(
        arguments.scratchpad_root
    )
    unittest.main(argv=[sys.argv[0], *unittest_arguments])
