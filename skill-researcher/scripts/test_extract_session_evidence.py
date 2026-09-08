#!/usr/bin/env python3
"""Behavior tests for bounded session evidence and declared skill use."""

from __future__ import annotations

import importlib.util
import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


SCRIPT_PATH = Path(__file__).with_name("extract_session_evidence.py")


def load_extractor() -> ModuleType:
    """Load the sibling extractor as a module for focused behavior tests."""
    spec = importlib.util.spec_from_file_location("extract_session_evidence", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load extractor module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


EXTRACTOR = load_extractor()


def skills(*names: str) -> dict[str, object]:
    """Build the known-skill mapping consumed by the extraction helper."""
    return {
        name: EXTRACTOR.SkillInfo(
            name=name,
            path=Path("/skills") / name / "SKILL.md",
            owner="user",
        )
        for name in names
    }


class AssistantDeclaredSkillRefsTests(unittest.TestCase):
    """Pin explicit assistant-declaration recognition and its exclusions."""

    def test_detects_dollar_prefixed_declaration(self) -> None:
        """Recognize the original dollar-prefixed declaration syntax."""
        actual = EXTRACTOR.assistant_declared_skill_refs(
            "I am using $plan-strict-work for the requested plan.",
            skills("plan-strict-work"),
        )
        self.assertEqual(actual, ["plan-strict-work"])

    def test_detects_backticked_bare_declaration(self) -> None:
        """Recognize the common backticked declaration syntax."""
        actual = EXTRACTOR.assistant_declared_skill_refs(
            "I’m using the `plan-strict-work` skill because this is a plan request.",
            skills("plan-strict-work"),
        )
        self.assertEqual(actual, ["plan-strict-work"])

    def test_detects_plain_bare_declaration(self) -> None:
        """Recognize an unquoted known skill after a declaration verb."""
        actual = EXTRACTOR.assistant_declared_skill_refs(
            "I will invoke plan-strict-work for this task.",
            skills("plan-strict-work"),
        )
        self.assertEqual(actual, ["plan-strict-work"])

    def test_ignores_catalog_mentions_without_declaration(self) -> None:
        """Do not turn an injected-style catalog listing into live use."""
        actual = EXTRACTOR.assistant_declared_skill_refs(
            "Available skills:\n- plan-strict-work\n- implement-strict-work",
            skills("plan-strict-work", "implement-strict-work"),
        )
        self.assertEqual(actual, [])

    def test_ignores_negated_declaration(self) -> None:
        """Do not treat an explicit refusal as a declaration of use."""
        actual = EXTRACTOR.assistant_declared_skill_refs(
            "I will not use `plan-strict-work` for this request.",
            skills("plan-strict-work"),
        )
        self.assertEqual(actual, [])

    def test_does_not_borrow_use_verb_from_prior_clause(self) -> None:
        """Do not attach a later comparison mention to an earlier declaration."""
        actual = EXTRACTOR.assistant_declared_skill_refs(
            "I will use `plan-strict-work`. I compared `implement-strict-work` too.",
            skills("plan-strict-work", "implement-strict-work"),
        )
        self.assertEqual(actual, ["plan-strict-work"])

    def test_does_not_match_skill_name_prefix(self) -> None:
        """Keep shorter names from colliding with hyphenated skill names."""
        actual = EXTRACTOR.assistant_declared_skill_refs(
            "I am using `plan-strict-work` now.",
            skills("plan", "plan-strict-work"),
        )
        self.assertEqual(actual, ["plan-strict-work"])


class NestedGoalEvidenceTests(unittest.TestCase):
    """Exercise nested evidence through the owning session extractor."""

    def setUp(self) -> None:
        scratch = SCRIPT_PATH.resolve().parents[2] / ".scratchpad"
        self.temporary = tempfile.TemporaryDirectory(prefix="nested-goal-test-", dir=scratch)
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.transcript = self.folder / "session.jsonl"
        self.skills_root = self.folder / "skills"
        self.skills_root.mkdir()

    @staticmethod
    def call(source: str, call_id: str = "outer") -> dict:
        return {"type": "response_item", "payload": {
            "type": "custom_tool_call", "name": "exec", "status": "completed",
            "call_id": call_id, "input": source,
        }}

    @staticmethod
    def output(value: object, call_id: str = "outer") -> dict:
        return {"type": "response_item", "payload": {
            "type": "custom_tool_call_output", "call_id": call_id, "output": value,
        }}

    def extract(self, records: list[dict]) -> dict:
        # Keep fixtures UTF-8 and LF-delimited on every host, matching source locators.
        self.transcript.write_bytes(b"\n".join(json.dumps(row).encode("utf-8") for row in records) + b"\n")
        return self.read_transcript()

    def read_transcript(self) -> dict:
        return EXTRACTOR.extract(argparse.Namespace(
            transcript=self.transcript, skills_root=self.skills_root,
            max_message_chars=4000, max_total_message_chars=90000,
            max_tool_output_chars=1200, exclude_skill=[],
        ))

    def test_literal_properties_and_result_forwarding(self) -> None:
        sources = [
            'text(await tools.update_goal({status:"complete"}));',
            'text(await tools /* owner */ . update_goal({"status":"complete",}));',
            "text(await tools.update_goal({'status':'complete'}));",
            'const result = await tools.update_goal({status:"complete"}); text(result);',
        ]
        for source in sources:
            with self.subTest(source=source):
                context = self.extract([self.call(source), self.output({"goal": {"status": "complete"}})])["goal_context"]
                self.assertTrue(context["successful_completion_detected"])
                self.assertTrue(context["nested_extraction"]["complete_within_scope"])
                self.assertEqual(context["events"][0]["output_confirmation"], "confirmed")
                self.assertEqual(context["events"][0]["output_lines"], [2])

    def test_inert_text_is_not_a_call_site(self) -> None:
        source = """const quoted = 'tools.update_goal({status:"complete"})';
        // tools.update_goal({status:"complete"})
        /* tools.update_goal({status:"blocked"}) */
        const template = `tools.update_goal({status:"complete"})`;
        """
        message = {"type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": source}]}}
        context = self.extract([message, self.call(source)])["goal_context"]
        self.assertEqual(context["events"], [])
        self.assertTrue(context["nested_extraction"]["complete_within_scope"])

    def test_argument_notes_do_not_override_the_status_property(self) -> None:
        source = '''text(await tools.update_goal({note: 'status:"complete"', nested: {status:"complete"}, /* status:"complete" */ status:"blocked"}));'''
        context = self.extract([self.call(source), self.output({"goal": {"status": "blocked"}})])["goal_context"]
        event = context["events"][0]
        self.assertEqual(event["arguments"], {"status": "blocked"})
        self.assertEqual(event["output_confirmation"], "confirmed")
        self.assertFalse(context["successful_completion_detected"])

    def test_unsupported_syntax_reports_incomplete_coverage(self) -> None:
        sources = [
            'const pattern = /tools.update_goal({status:"complete"})/;',
            '`value ${tools.update_goal({status:"complete"})}`',
            'tools.update_goal({status: chosen})',
            'tools.update_goal({status:"blocked",status:"complete"})',
            'tools.update_goal({status:[]})',
            'tools.update_goal({status:"complete"}',
            'tools.update_goal({status:"complete", note: "\\N{SPACE}"})',
        ]
        for source in sources:
            with self.subTest(source=source):
                context = self.extract([self.call(source)])["goal_context"]
                self.assertFalse(context["nested_extraction"]["complete_within_scope"])
                self.assertTrue(context["nested_extraction"]["issues"])
                self.assertFalse(context["successful_completion_detected"])

    def test_control_flow_and_multiple_sites_cannot_borrow_one_output(self) -> None:
        sources = [
            'if (false) { tools.update_goal({status:"complete"}); }',
            'if (false) { tools.update_goal({status:"complete"}); } text(await tools.update_goal({status:"complete"}));',
            'function unused() { return tools.update_goal({status:"complete"}); }',
            'await tools.update_goal({status:"complete"});',
        ]
        for source in sources:
            with self.subTest(source=source):
                context = self.extract([self.call(source), self.output({"goal": {"status": "complete"}})])["goal_context"]
                self.assertTrue(context["events"])
                self.assertEqual({event["output_confirmation"] for event in context["events"]}, {"unattributed-output"})
                self.assertFalse(context["successful_completion_detected"])

    def test_supported_typed_result_encodings(self) -> None:
        goal = {"status": "complete", "goal_id": "selected", "objective": "x" * 7000}
        values = [
            {"goal": goal}, json.dumps({"goal": goal}),
            {"goal": json.dumps(goal)},
            {"content": [{"type": "text", "text": json.dumps({"goal": goal})}]},
        ]
        for value in values:
            with self.subTest(kind=type(value).__name__):
                context = self.extract([self.call('text(await tools.update_goal({status:"complete"}));'), self.output(value)])["goal_context"]
                self.assertTrue(context["successful_completion_detected"])
                observed = context["completion_outputs"][0]["output"]["goal"]
                self.assertEqual(observed["goal_id"], "selected")
                self.assertTrue(observed["objective_truncated"])

    def test_failure_and_example_outputs_never_confirm(self) -> None:
        examples = [
            ('Example only: {"goal":{"status":"complete"}}', "unsupported-output"),
            ({"ok": False, "error": {"status": "complete"}}, "failed-output"),
            ({"success": False, "goal": {"status": "complete"}}, "failed-output"),
            ({"exit_code": 9, "goal": {"status": "complete"}}, "failed-output"),
            ({"isError": True, "content": [{"type": "text", "text": '{"goal":{"status":"complete"}}'}]}, "failed-output"),
            ({"status": "complete"}, "unsupported-output"),
            ({"ok": "true", "goal": {"status": "complete"}}, "unsupported-output"),
            ({"exit_code": False, "goal": {"status": "complete"}}, "unsupported-output"),
            ({"status": [], "goal": {"status": "complete"}}, "unsupported-output"),
            ({"goal": {"status": "complete"}, "content": [{"type": "text", "text": '{"goal":{"status":"blocked"}}'}]}, "unsupported-output"),
            ('{"goal":{"status":"blocked","status":"complete"}}', "unsupported-output"),
            ({"goal": {"status": "blocked"}}, "status-mismatch"),
        ]
        for value, expected in examples:
            with self.subTest(value=value):
                context = self.extract([self.call('text(await tools.update_goal({status:"complete"}));'), self.output(value)])["goal_context"]
                self.assertEqual(context["events"][0]["output_confirmation"], expected)
                self.assertFalse(context["successful_completion_detected"])

    def test_missing_duplicate_and_out_of_order_outputs(self) -> None:
        call = self.call('text(await tools.update_goal({status:"complete"}));')
        output = self.output({"goal": {"status": "complete"}})
        for records, expected in [
            ([call], "missing-output"),
            ([call, output, self.output({"goal": {"status": "blocked"}})], "ambiguous-correlation"),
            ([call, call, output], "ambiguous-correlation"),
            ([output, call], "ambiguous-correlation"),
        ]:
            with self.subTest(expected=expected, count=len(records)):
                context = self.extract(records)["goal_context"]
                self.assertEqual({event["output_confirmation"] for event in context["events"]}, {expected})
                self.assertFalse(context["successful_completion_detected"])

    def test_direct_goal_events_keep_their_existing_contract(self) -> None:
        records = [
            {"type": "event_msg", "payload": {"type": "thread_goal_updated", "goal": {"status": "active"}}},
            {"type": "response_item", "payload": {"type": "function_call", "name": "update_goal", "call_id": "direct", "arguments": '{"status":"complete"}'}},
            {"type": "response_item", "payload": {"type": "function_call_output", "call_id": "direct", "output": '{"goal":{"status":"complete"}}'}},
        ]
        context = self.extract(records)["goal_context"]
        self.assertEqual([event["kind"] for event in context["events"]], ["thread_goal_updated", "goal_tool_call", "goal_tool_output"])
        self.assertTrue(context["successful_completion_detected"])

    def test_lf_anchors_and_malformed_input_visibility(self) -> None:
        call = self.call('text(await tools.update_goal({status:"complete"}));')
        output = self.output({"goal": {"status": "complete"}})
        self.transcript.write_bytes(('{}\r{}\n[]\nnull\n{\n' + json.dumps(call) + '\n' + json.dumps(output) + '\n').encode())
        report = self.read_transcript()
        self.assertEqual(report["transcript"]["malformed_lines"], [1, 2, 3, 4])
        self.assertEqual(report["goal_context"]["events"][0]["line"], 5)
        self.assertEqual(report["goal_context"]["events"][0]["output_lines"], [6])
        self.assertFalse(report["goal_context"]["nested_extraction"]["complete_within_scope"])

    def test_cli_success_and_normalized_missing_input(self) -> None:
        self.extract([self.call('text(await tools.update_goal({status:"complete"}));'), self.output({"goal": {"status": "complete"}})])
        command = [sys.executable, "-B", str(SCRIPT_PATH), "--skills-root", str(self.skills_root), "--transcript"]
        success = subprocess.run(command + [str(self.transcript)], capture_output=True, text=True)
        self.assertEqual(success.returncode, 0, success.stderr)
        self.assertTrue(json.loads(success.stdout)["goal_context"]["successful_completion_detected"])
        failure = subprocess.run(command + [str(self.folder / "missing.jsonl")], capture_output=True, text=True)
        self.assertEqual(failure.returncode, 2)
        self.assertEqual(failure.stdout, "")
        self.assertNotIn(str(Path.home()), failure.stderr)
        self.assertIn("~/", failure.stderr)


if __name__ == "__main__":
    unittest.main()
