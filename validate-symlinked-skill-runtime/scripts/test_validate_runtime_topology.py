#!/usr/bin/env python3
"""Exercise the validator's observable CLI behavior using disposable targets."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("validate_runtime_topology.py").resolve()
SCRATCH = SCRIPT.parents[2] / ".scratchpad"

TARGET = '''import json
import os
from pathlib import Path
import sys

mode = sys.argv[1]
runtime = Path(os.environ["CODEX_HOME"])
repository = Path(os.environ["CANONICAL_SKILL_REPOSITORY"])
output = Path(os.environ["TASK_OUTPUT_ROOT"])
topology = os.environ["TOPOLOGY_NAME"]
package = Path(__file__).parent
external = Path(os.environ["TEST_EXTERNAL_ROOT"])
marker = output / "marker.txt"
if mode in {"directory_artifact", "implicit_parent"}:
    marker = output / "bundle" / "nested" / "marker.txt"
    marker.parent.mkdir(parents=True)
elif mode == "declared_escape":
    marker = external / (topology + ".txt")
if mode != "read_only":
    marker.write_text(topology if mode == "artifact_mismatch" else "equal bytes", encoding="utf-8")
if mode == "empty_repository_directory":
    (repository / "unexpected-empty").mkdir(exist_ok=True)
if mode == "empty_runtime_directory":
    (runtime / "unexpected-empty").mkdir(exist_ok=True)
if mode == "source_file_mutation":
    (repository / "state.txt").write_text("changed", encoding="utf-8")
if mode == "mode_mutation":
    (runtime / "state.txt").chmod(0o600)
if mode in {"copied_file_mutation", "copied_directory_mutation"} and topology == "copied":
    if mode == "copied_file_mutation":
        (package / "unexpected.txt").write_text("changed", encoding="utf-8")
    else:
        (package / "unexpected-empty").mkdir()
if mode == "unreported_output":
    (output / "unreported.txt").write_text("extra", encoding="utf-8")
if mode == "unreported_directory":
    (output / "unreported-empty").mkdir()
if mode == "unobserved_external":
    (external / (topology + ".txt")).write_text("outside observed roots", encoding="utf-8")
if mode == "escaping_link":
    (output / "outside").symlink_to(external, target_is_directory=True)

report = {
    "runtime_root": str(repository if mode == "wrong_authority" else runtime),
    "repository_root": str(repository),
    "package_root": str(package),
    "runtime_state": (runtime / "state.txt").read_text(encoding="utf-8"),
    "repository_state": (repository / "state.txt").read_text(encoding="utf-8"),
    "resource": (package / "resource.txt").read_text(encoding="utf-8"),
    "sibling": (package.parent / "example-sibling" / "resource.txt").read_text(encoding="utf-8"),
    "side_effects": [] if mode == "read_only" else [str(marker)],
    "topology": topology,
}
if mode == "directory_artifact":
    report["side_effects"] = [str(output / "bundle")]
if mode == "escaping_link":
    report["side_effects"].append(str(output / "outside"))
if mode == "nested_result_mismatch":
    report["result"] = {"topology": "different" if topology == "copied" else "usual"}
if mode == "embedded_path_mismatch":
    report["result"] = "message: " + str(package)
if mode == "path_prefix_mismatch":
    report["result"] = str(package) + "-different"
if mode in {"portable_paths", "mixed_path_spelling"}:
    if mode == "portable_paths" or topology == "copied":
        for key in ("runtime_root", "repository_root", "package_root"):
            report[key] = "~/" + Path(report[key]).relative_to(Path.home()).as_posix()
        report["side_effects"] = ["~/" + marker.relative_to(Path.home()).as_posix()]
if mode == "stderr_failure":
    print("diagnostic at " + str(package), file=sys.stderr)
print(json.dumps(report))
'''


class RuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="runtime-cli-test-", dir=SCRATCH)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repository = self.root / "repository"
        self.package = self.repository / "example-skill"
        self.package.mkdir(parents=True)
        (self.package / "entry.py").write_text(TARGET, encoding="utf-8")
        (self.package / "resource.txt").write_text("package", encoding="utf-8")
        self.sibling = self.repository / "example-sibling"
        self.sibling.mkdir()
        (self.sibling / "resource.txt").write_text("sibling", encoding="utf-8")
        self.runtime = self.root / "runtime"
        self.runtime.mkdir()
        for root in (self.repository, self.runtime):
            (root / "state.txt").write_text("state", encoding="utf-8")
            (root / "state.txt").chmod(0o644)
        self.external = self.root / "external"
        self.external.mkdir()

    def run_case(self, mode: str, success: bool, siblings: bool = True) -> dict[str, object]:
        args = [
            sys.executable, str(SCRIPT), "--canonical-repository", str(self.repository),
            "--source-package", str(self.package), "--entry-point", "entry.py",
            "--runtime-root", str(self.runtime), "--target-arg=" + mode,
        ]
        if siblings:
            args.extend(["--sibling-package", "example-sibling=" + str(self.sibling)])
        result = subprocess.run(
            args, env=dict(os.environ, TEST_EXTERNAL_ROOT=str(self.external)),
            capture_output=True, text=True, check=False, timeout=20,
        )
        self.assertEqual(result.returncode, 0 if success else 1, result.stderr + result.stdout)
        self.assertEqual(result.stderr, "")
        self.assertNotIn(str(Path.home()), result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "success" if success else "failure")
        self.assertTrue(report["received"]["fixture_removed"])
        self.assertFalse((self.repository / ".scratchpad").exists())
        return report

    def test_real_resources_and_authorities_have_four_topology_parity(self) -> None:
        report = self.run_case("baseline", True)
        self.assertEqual(report["received"]["successful_topologies"], 4)
        self.assertEqual(report["received"]["unique_artifact_states"], 1)
        self.assertEqual(report["not_run_topologies"], [])
        self.assertEqual(
            {row["normalized_output"]["sibling"] for row in report["topologies"]}, {"sibling"}
        )

    def test_read_only_target_does_not_need_a_marker(self) -> None:
        report = self.run_case("read_only", True)
        self.assertTrue(all(row["normalized_output"]["side_effects"] == [] for row in report["topologies"]))
        self.assertTrue(all(set(row["artifact_state"]) == {"."} for row in report["topologies"]))

    def test_changed_artifact_bytes_fail_even_when_reported_json_matches(self) -> None:
        report = self.run_case("artifact_mismatch", False)
        self.assertEqual(report["received"]["unique_normalized_outputs"], 1)
        self.assertEqual(report["received"]["unique_artifact_states"], 4)

    def test_nested_topology_result_is_preserved(self) -> None:
        report = self.run_case("nested_result_mismatch", False)
        values = {row["normalized_output"]["result"]["topology"] for row in report["topologies"]}
        self.assertEqual(values, {"different", "usual"})

    def test_embedded_paths_and_shared_prefixes_are_not_normalized(self) -> None:
        for mode in ("embedded_path_mismatch", "path_prefix_mismatch"):
            with self.subTest(mode=mode):
                report = self.run_case(mode, False)
                self.assertGreater(report["received"]["unique_normalized_outputs"], 1)

    def test_empty_repository_directory_fails_and_stops_later_runs(self) -> None:
        report = self.run_case("empty_repository_directory", False)
        self.assertFalse(report["received"]["repository_unchanged"])
        self.assertEqual(len(report["topologies"]), 1)
        self.assertEqual(report["not_run_topologies"], ["copied", "relative-symlink", "absolute-symlink"])

    def test_empty_runtime_directory_is_observed(self) -> None:
        report = self.run_case("empty_runtime_directory", False)
        self.assertFalse(report["received"]["runtime_unchanged"])

    def test_file_mutation_remains_protected(self) -> None:
        report = self.run_case("source_file_mutation", False)
        self.assertFalse(report["received"]["repository_unchanged"])

    def test_permission_changes_are_observed(self) -> None:
        report = self.run_case("mode_mutation", False)
        self.assertFalse(report["received"]["runtime_unchanged"])

    def test_copied_fixture_mutations_outside_task_output_fail(self) -> None:
        for mode in ("copied_file_mutation", "copied_directory_mutation"):
            with self.subTest(mode=mode):
                report = self.run_case(mode, False)
                self.assertTrue(report["received"]["repository_unchanged"])
                copied = report["topologies"][-1]
                self.assertEqual(copied["topology"], "copied")
                self.assertFalse(copied["fixture_writes_valid"])
                self.assertTrue(copied["fixture_changes_outside_task_output"]["added"])

    def test_unreported_output_files_and_empty_directories_fail(self) -> None:
        for mode in ("unreported_output", "unreported_directory"):
            with self.subTest(mode=mode):
                report = self.run_case(mode, False)
                self.assertTrue(all(row["unreported_output_paths"] for row in report["topologies"]))

    def test_declared_directory_artifacts_and_implicit_parents_are_supported(self) -> None:
        for mode in ("directory_artifact", "implicit_parent"):
            with self.subTest(mode=mode):
                self.run_case(mode, True)

    def test_declared_escaping_file_and_symlink_fail(self) -> None:
        for mode in ("declared_escape", "escaping_link"):
            with self.subTest(mode=mode):
                report = self.run_case(mode, False)
                self.assertTrue(all(not row["side_effects_valid"] for row in report["topologies"]))

    def test_external_write_detection_limit_is_explicit(self) -> None:
        report = self.run_case("unobserved_external", True)
        self.assertEqual(len(list(self.external.iterdir())), 4)
        self.assertEqual(report["observation_scope"]["external_writes"], "not_observed")
        self.assertFalse(report["observation_scope"]["preventive_sandbox"])

    def test_home_relative_and_mixed_path_spellings_compare_equally(self) -> None:
        for mode in ("portable_paths", "mixed_path_spelling"):
            with self.subTest(mode=mode):
                self.run_case(mode, True)

    def test_authority_mismatch_is_not_normalized_into_parity(self) -> None:
        report = self.run_case("wrong_authority", False)
        self.assertTrue(all(not row["runtime_valid"] for row in report["topologies"]))

    def test_missing_sibling_fails_in_each_deployed_fixture(self) -> None:
        report = self.run_case("baseline", False, siblings=False)
        self.assertEqual([row["status"] for row in report["topologies"]], ["success", "failure", "failure", "failure"])

    def test_stderr_failure_remains_a_failure_and_renders_home_paths(self) -> None:
        report = self.run_case("stderr_failure", False)
        self.assertTrue(all("~/" in row["stderr"] for row in report["topologies"]))

    def test_existing_scratch_content_survives_validation(self) -> None:
        scratch = self.repository / ".scratchpad"
        scratch.mkdir()
        sentinel = scratch / "existing.txt"
        sentinel.write_text("preserve", encoding="utf-8")
        args = [
            sys.executable, str(SCRIPT), "--canonical-repository", str(self.repository),
            "--source-package", str(self.package), "--entry-point", "entry.py",
            "--runtime-root", str(self.runtime), "--target-arg=read_only",
            "--sibling-package=example-sibling=" + str(self.sibling),
        ]
        result = subprocess.run(args, env=dict(os.environ, TEST_EXTERNAL_ROOT=str(self.external)), capture_output=True, text=True, check=False, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve")
        self.assertEqual(list(scratch.iterdir()), [sentinel])

    def test_self_test_requires_an_explicit_scratch_destination(self) -> None:
        result = subprocess.run([sys.executable, str(SCRIPT), "--self-test"], capture_output=True, text=True, check=False, timeout=20)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("--scratch-root", result.stderr)

    def test_explicit_scratch_root_preserves_existing_content(self) -> None:
        scratch = self.root / "selected-scratch"
        scratch.mkdir()
        sentinel = scratch / "existing.txt"
        sentinel.write_text("preserve", encoding="utf-8")
        args = [
            sys.executable, str(SCRIPT), "--canonical-repository", str(self.repository),
            "--source-package", str(self.package), "--entry-point", "entry.py",
            "--runtime-root", str(self.runtime), "--target-arg=read_only",
            "--sibling-package=example-sibling=" + str(self.sibling),
            "--scratch-root", str(scratch),
        ]
        result = subprocess.run(
            args, env=dict(os.environ, TEST_EXTERNAL_ROOT=str(self.external)),
            capture_output=True, text=True, check=False, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(list(scratch.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve")

    def test_scratch_inside_a_selected_package_is_rejected_before_execution(self) -> None:
        result = subprocess.run(
            [
                sys.executable, str(SCRIPT), "--canonical-repository", str(self.repository),
                "--source-package", str(self.package), "--entry-point", "entry.py",
                "--runtime-root", str(self.runtime), "--target-arg=source_file_mutation",
                "--scratch-root", str(self.package),
            ], capture_output=True, text=True, check=False, timeout=20,
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "failure")
        self.assertEqual((self.repository / "state.txt").read_text(encoding="utf-8"), "state")
        self.assertFalse((self.repository / ".scratchpad").exists())


if __name__ == "__main__":
    unittest.main()
