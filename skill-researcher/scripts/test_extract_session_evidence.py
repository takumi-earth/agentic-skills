#!/usr/bin/env python3
"""Behavior tests for declared skill-use extraction."""

from __future__ import annotations

import importlib.util
import sys
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


if __name__ == "__main__":
    unittest.main()
