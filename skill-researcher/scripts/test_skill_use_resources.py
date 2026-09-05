#!/usr/bin/env python3
"""Exercise optional evidence resources through their public CLI contracts."""

from __future__ import annotations

import json
import os
from pathlib import Path
import runpy
import shlex
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parent
SCRATCH = SCRIPTS.parents[1] / ".scratchpad"


def response(kind: str, **fields: object) -> dict[str, object]:
    return {"type": "response_item", "payload": {"type": kind, **fields}}


class ResourceTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="skill-use-", dir=SCRATCH)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.body = self.root / "unavailable" / "SKILL.md"
        self.catalog = self.root / "catalog.json"
        self.transcript = self.root / "session.jsonl"
        self.set_catalog([{"name": "example-skill", "path": str(self.body)}])
        self.set_transcript([])

    def set_catalog(self, entries: object) -> None:
        self.catalog.write_text(json.dumps({"skills": entries}), encoding="utf-8")

    def set_transcript(self, records: list[object]) -> None:
        self.transcript.write_text(
            "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
        )

    def snapshot(self) -> dict[str, object]:
        return {
            str(path.relative_to(self.root)): os.readlink(path) if path.is_symlink() else path.read_bytes()
            for path in self.root.rglob("*") if path.is_symlink() or path.is_file()
        }

    def run_cli(self, script: str, *arguments: str, success: bool = True) -> dict[str, object] | str:
        before = self.snapshot()
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / script), *arguments],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(self.snapshot(), before, "resource modified its inputs or created an artifact")
        self.assertNotIn(str(Path.home()), result.stdout + result.stderr)
        self.assertEqual(result.returncode, 0 if success else 2, result.stderr)
        if success:
            self.assertEqual(result.stderr, "")
            return json.loads(result.stdout)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result.stderr

    def catalog_report(self, success: bool = True) -> dict[str, object] | str:
        return self.run_cli(
            "resolve_catalog_skill_use.py", "--catalog", str(self.catalog),
            "--transcript", str(self.transcript), success=success,
        )

    def command(self, command: str, custom: bool = False) -> dict[str, object]:
        if custom:
            return response("custom_tool_call", name="exec", input=command)
        return response("function_call", name="exec_command", arguments=json.dumps({"cmd": command}))

    def test_catalog_availability_does_not_require_an_installed_skill(self) -> None:
        report = self.catalog_report()
        self.assertEqual(len(report["catalog"]), 1)
        for field in ("assistant_references", "tool_path_mentions", "read_command_candidates"):
            self.assertEqual(report[field], [])
        self.assertFalse(report["evidence_limits"]["current_topology_consulted"])
        self.assertFalse(self.body.exists())

    def test_exact_assistant_references_are_neither_declarations_nor_reads(self) -> None:
        self.set_transcript([
            response("message", role="developer", content=[{"type": "input_text", "text": "$example-skill"}]),
            response("message", role="assistant", content=[{"type": "output_text", "text": "$example-skill-extra $unknown"}]),
            response("message", role="assistant", content=[{"type": "output_text", "text": "Do not use `$example-skill`."}]),
            response("message", role="assistant", content=[{"type": "metadata", "text": "$example-skill"}]),
        ])
        report = self.catalog_report()
        self.assertEqual([item["line"] for item in report["assistant_references"]], [3])
        self.assertEqual(report["read_command_candidates"], [])
        self.assertFalse(report["evidence_limits"]["behavioral_use_evaluated"])

    def test_duplicate_names_keep_path_ambiguity_and_identical_entries_deduplicate(self) -> None:
        other = self.root / "other" / "SKILL.md"
        self.set_catalog([
            {"name": "example-skill", "path": str(self.body)},
            {"name": "example-skill", "path": str(other)},
            {"name": "example-skill", "path": "~/" + self.body.relative_to(Path.home()).as_posix()},
        ])
        self.set_transcript([response("message", role="assistant", content="$example-skill")])
        report = self.catalog_report()
        self.assertEqual(len(report["catalog"]), 2)
        reference = report["assistant_references"][0]
        self.assertTrue(reference["ambiguous"])
        self.assertEqual(len(reference["candidate_paths"]), 2)
        self.assertEqual(report, self.catalog_report())

    def test_native_and_custom_direct_read_commands(self) -> None:
        operand = shlex.quote(str(self.body))
        commands = [
            f"cat {operand}", f"cat -n -- {operand}", f"head -n 10 {operand}",
            f"tail --lines=3 {operand}", f"sed -n '1,12p' {operand}",
        ]
        for custom in (False, True):
            with self.subTest(custom=custom):
                self.set_transcript([self.command(command, custom) for command in commands])
                report = self.catalog_report()
                self.assertEqual(len(report["read_command_candidates"]), len(commands))
                self.assertEqual(len(report["tool_path_mentions"]), len(commands))
                self.assertEqual(report["assistant_references"], [])
                self.assertFalse(report["evidence_limits"]["successful_reads_verified"])

    def test_path_suffixes_and_prefixes_do_not_match_catalog_body(self) -> None:
        self.set_transcript([
            self.command(f"cat {self.body}.backup"),
            self.command(f"cat /prefix{self.body}"),
            self.command(f"cat {self.body}/nested"),
        ])
        report = self.catalog_report()
        self.assertEqual(report["tool_path_mentions"], [])
        self.assertEqual(report["read_command_candidates"], [])

    def test_printing_and_unsupported_readers_remain_mentions(self) -> None:
        commands = [
            f'python3 -c "print(\'{self.body}\')"',
            f'printf "cat {self.body}"',
            f"rg pattern {self.body}",
            f"cat --help {self.body}",
            f"sed -i '1p' {self.body}",
        ]
        self.set_transcript([self.command(command) for command in commands])
        report = self.catalog_report()
        self.assertEqual(len(report["tool_path_mentions"]), len(commands))
        self.assertEqual(report["read_command_candidates"], [])

    def test_shell_composition_and_javascript_are_never_executed_or_inferred(self) -> None:
        marker = self.root / "must-not-exist"
        self.set_transcript([
            self.command(f"cat {self.body}; touch {marker}"),
            self.command(f'cat "$(printf %s {self.body})"'),
            self.command(f"await tools.exec_command({json.dumps({'cmd': f'cat {self.body}'})})", custom=True),
        ])
        report = self.catalog_report()
        self.assertEqual(len(report["tool_path_mentions"]), 3)
        self.assertEqual(report["read_command_candidates"], [])
        self.assertFalse(marker.exists())

    def test_lexical_symlink_alias_matches_without_collapsing_into_current_target(self) -> None:
        source = self.root / "source"
        source.mkdir()
        (source / "SKILL.md").write_text("current body", encoding="utf-8")
        alias = self.root / "alias"
        alias.symlink_to("source", target_is_directory=True)
        lexical = alias / "SKILL.md"
        self.set_catalog([{"name": "example-skill", "path": "~/" + lexical.relative_to(Path.home()).as_posix()}])
        self.set_transcript([
            self.command(f"cat {lexical}"),
            self.command(f"cat {source / 'SKILL.md'}"),
        ])
        report = self.catalog_report()
        self.assertEqual([item["line"] for item in report["read_command_candidates"]], [1])
        self.assertEqual([item["line"] for item in report["tool_path_mentions"]], [1])
        self.assertFalse(report["evidence_limits"]["current_topology_consulted"])

    def test_relative_catalog_path_does_not_borrow_current_working_directory(self) -> None:
        self.set_catalog([{"name": "example-skill", "path": "relative/SKILL.md"}])
        self.set_transcript([self.command("cat ./relative/SKILL.md")])
        report = self.catalog_report()
        self.assertEqual(report["catalog"][0]["path"], "relative/SKILL.md")
        self.assertEqual(len(report["read_command_candidates"]), 1)
        self.assertEqual(len(report["tool_path_mentions"]), 1)

    def test_namespaced_native_calls_and_quoted_path_spaces(self) -> None:
        body = self.root / "with spaces" / "SKILL.md"
        self.set_catalog([{"name": "plugin:example-skill", "path": str(body)}])
        self.set_transcript([
            response("message", role="assistant", content="$plugin:example-skill"),
            response("function_call", name="functions.exec_command", arguments={"cmd": f"cat {shlex.quote(str(body))}"}),
            response("function_call_output", name="exec_command", output=f"cat {body}"),
        ])
        report = self.catalog_report()
        self.assertEqual(len(report["assistant_references"]), 1)
        self.assertEqual([item["line"] for item in report["read_command_candidates"]], [2])

    def test_bad_typed_payloads_return_input_errors(self) -> None:
        for record in (
            {"type": "response_item", "payload": []},
            {"type": "response_item", "payload": {"type": []}},
            response("function_call", name=[], arguments={}),
        ):
            with self.subTest(record=record):
                self.set_transcript([record])
                self.assertIn("line 1", self.catalog_report(success=False))

    def test_unknown_message_blocks_and_malformed_shell_do_not_imply_use(self) -> None:
        self.set_transcript([
            response("message", role="assistant", content=[{"type": [], "text": "$example-skill"}]),
            self.command(f'cat "{self.body}'),
        ])
        report = self.catalog_report()
        self.assertEqual(report["assistant_references"], [])
        self.assertEqual(report["read_command_candidates"], [])

    def test_malformed_catalog_shapes_fail_without_partial_json(self) -> None:
        for value in ([], {}, {"skills": "text"}, {"skills": [False]}, {"skills": [{"name": "x", "path": "wrong"}]}):
            with self.subTest(value=value):
                self.catalog.write_text(json.dumps(value), encoding="utf-8")
                self.catalog_report(success=False)

    def test_malformed_json_and_nonobject_transcript_records_fail_with_line(self) -> None:
        for line in ("[]", "null", '"text"', "{"):
            with self.subTest(line=line):
                self.transcript.write_text('{"type":"session_meta"}\n' + line + "\n", encoding="utf-8")
                self.assertIn("line 2", self.catalog_report(success=False))

    def test_missing_and_non_utf8_inputs_have_normalized_diagnostics(self) -> None:
        self.catalog.unlink()
        self.catalog_report(success=False)
        self.catalog.write_bytes(b"\xff")
        self.catalog_report(success=False)

    def test_current_topology_keeps_copies_aliases_and_content_separate(self) -> None:
        for name, content in (("source", "shared body"), ("copy", "shared body"), ("changed", "other body")):
            package = self.root / name
            package.mkdir()
            (package / "SKILL.md").write_text(content, encoding="utf-8")
            (package / "extra.txt").write_text(name, encoding="utf-8")
        (self.root / "relative").symlink_to("source", target_is_directory=True)
        (self.root / "absolute").symlink_to(self.root / "source", target_is_directory=True)
        (self.root / "ancestor").symlink_to(self.root, target_is_directory=True)
        paths = {
            "source": self.root / "source", "copy": self.root / "copy",
            "changed": self.root / "changed", "relative": self.root / "relative",
            "absolute": self.root / "absolute", "ancestor": self.root / "ancestor" / "source",
        }
        args = [arg for name, path in paths.items() for arg in ("--projection", f"{name}={path}")]
        report = self.run_cli("resolve_skill_topology.py", *args)
        items = {item["label"]: item for item in report["projections"]}
        original = items["source"]
        for label in ("relative", "absolute", "ancestor"):
            self.assertEqual(items[label]["canonical_body"], original["canonical_body"])
            self.assertEqual(items[label]["filesystem_identity"], original["filesystem_identity"])
            self.assertTrue(items[label]["lexical_symlinks"])
        self.assertEqual(items["relative"]["lexical_symlinks"][-1]["target"], "source")
        self.assertTrue(items["absolute"]["lexical_symlinks"][-1]["target"].startswith("~/"))
        self.assertNotEqual(items["copy"]["filesystem_identity"], original["filesystem_identity"])
        self.assertNotEqual(items["copy"]["canonical_body"], original["canonical_body"])
        self.assertEqual(items["copy"]["body_sha256"], original["body_sha256"])
        self.assertNotEqual(items["changed"]["body_sha256"], original["body_sha256"])
        self.assertEqual(len(report["content_groups"]), 2)
        self.assertEqual(report["evidence_limits"], {"time_scope": "current", "content_scope": "SKILL.md"})

    def test_body_symlink_is_reported_when_projection_names_skill_file(self) -> None:
        original = self.root / "body.md"
        original.write_text("body", encoding="utf-8")
        link = self.root / "SKILL.md"
        link.symlink_to("body.md")
        report = self.run_cli("resolve_skill_topology.py", "--projection", f"body={link}")
        self.assertEqual(report["projections"][0]["lexical_symlinks"][-1]["target"], "body.md")

    def test_topology_errors_emit_no_partial_report(self) -> None:
        valid = self.root / "SKILL.md"
        valid.write_text("body", encoding="utf-8")
        cases = [
            ["--projection", "invalid"],
            ["--projection", f"same={valid}", "--projection", f"same={valid}"],
            ["--projection", f"valid={valid}", "--projection", f"missing={self.root / 'missing'}"],
        ]
        for args in cases:
            with self.subTest(args=args):
                self.run_cli("resolve_skill_topology.py", *args, success=False)

    def test_external_path_rendering_does_not_invent_a_home_alias(self) -> None:
        namespace = runpy.run_path(str(SCRIPTS / "resolve_skill_topology.py"), run_name="resource_test")
        self.assertEqual(namespace["display_path"](Path("/opt/example/SKILL.md")), "/opt/example/SKILL.md")


if __name__ == "__main__":
    unittest.main()
