#!/usr/bin/env python3
"""Behavior tests for the architectural-regression audit scripts."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIRECTORY))

import collect_source_evidence as collector
import collect_rust_call_inventory as call_inventory
import validate_verdict_packet as validator


SKILL_ROOT = SCRIPT_DIRECTORY.parent


def git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


class SourceEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="architecture-audit-")
        self.root = Path(self.temporary.name)
        self.repository = self.root / "repository"
        self.repository.mkdir()
        git(self.repository, "init", "--quiet")
        git(self.repository, "config", "user.email", "audit@example.invalid")
        git(self.repository, "config", "user.name", "Audit Fixture")
        source = self.repository / "src" / "policy.rs"
        source.parent.mkdir()
        source.write_text("const RESOLVER: &str = \"2\";\nfn policy() {\n    legacy();\n}\n", encoding="utf-8")
        git(self.repository, "add", "src/policy.rs")
        git(self.repository, "commit", "--quiet", "-m", "baseline")
        self.baseline = git(self.repository, "rev-parse", "HEAD")
        source.write_text("const RESOLVER: &str = \"3\";\nfn policy() {\n    current();\n}\n", encoding="utf-8")
        git(self.repository, "add", "src/policy.rs")
        git(self.repository, "commit", "--quiet", "-m", "current")
        source.write_text("const RESOLVER: &str = \"3\";\nfn policy() {\n    worktree();\n}\n", encoding="utf-8")
        self.spec_path = self.root / "source-spec.json"
        self.spec_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "repository": str(self.repository),
                    "checkpoints": [
                        {"id": "baseline", "revision": self.baseline},
                        {"id": "current", "revision": "WORKTREE"},
                    ],
                    "queries": [
                        {
                            "id": "baseline-resolver",
                            "checkpoint": "baseline",
                            "path": "src/policy.rs",
                            "patterns": ["RESOLVER: &str = \\\"(?P<resolver>[^\\\"]+)\\\""],
                            "match_mode": "source",
                            "context_before": 0,
                            "context_after": 0,
                            "required": True,
                        },
                        {
                            "id": "current-policy",
                            "checkpoint": "current",
                            "path": "src/policy.rs",
                            "patterns": ["worktree"],
                            "context_before": 1,
                            "context_after": 1,
                            "required": True,
                        },
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_collects_complete_historical_and_worktree_sources_deterministically(self) -> None:
        first = collector.collect(self.spec_path)
        second = collector.collect(self.spec_path)
        self.assertEqual(first, second)
        self.assertEqual(first["queries"][0]["snippets"][0]["lines"][0]["text"], 'const RESOLVER: &str = "2";')
        self.assertEqual(first["queries"][0]["captures"][0]["groups"], {"resolver": "2"})
        current_lines = first["queries"][1]["snippets"][0]["lines"]
        self.assertTrue(any("worktree();" in line["text"] for line in current_lines))
        markdown = collector.render_markdown(first)
        self.assertIn("baseline:src/policy.rs:1-1", markdown)
        self.assertIn("current:src/policy.rs:2-4", markdown)
        self.assertNotIn("diff --git", markdown.casefold())

    def test_rejects_required_query_without_a_match(self) -> None:
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        spec["queries"][0]["patterns"] = ["DOES_NOT_EXIST"]
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
        with self.assertRaisesRegex(collector.EvidenceError, "matched no lines"):
            collector.collect(self.spec_path)

    def test_rejects_repository_escape(self) -> None:
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        spec["queries"][0]["path"] = "../outside.rs"
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
        with self.assertRaisesRegex(collector.EvidenceError, "repository-relative"):
            collector.collect(self.spec_path)

    def test_scopes_query_before_semantic_test_module_boundary(self) -> None:
        source = self.repository / "src" / "policy.rs"
        source.write_text("fn production() { replace_item(); }\n#[cfg(test)]\nmod tests { fn test_case() { replace_item(); } }\n", encoding="utf-8")
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        spec["queries"] = [
            {
                "id": "production-replacement",
                "checkpoint": "current",
                "path": "src/policy.rs",
                "patterns": ["replace_item\\(\\)"],
                "scope_end_pattern": "(?m)^#\\[cfg\\(test\\)\\]\\s*\\nmod tests",
                "context_before": 0,
                "context_after": 0,
                "required": True,
            }
        ]
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
        evidence = collector.collect(self.spec_path)
        query = evidence["queries"][0]
        self.assertEqual(query["match_count"], 1)
        self.assertEqual(query["captures"][0]["line_start"], 1)
        self.assertEqual(query["scope"]["line_end"], 2)

    def test_checkpoint_can_select_another_repository(self) -> None:
        external = self.root / "external"
        external.mkdir()
        git(external, "init", "--quiet")
        git(external, "config", "user.email", "audit@example.invalid")
        git(external, "config", "user.name", "Audit Fixture")
        (external / "Cargo.toml").write_text('[workspace]\nresolver = "3"\n', encoding="utf-8")
        git(external, "add", "Cargo.toml")
        git(external, "commit", "--quiet", "-m", "external")
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        spec["checkpoints"].append({"id": "external", "revision": "WORKTREE", "repository": str(external)})
        spec["queries"] = [
            {
                "id": "external-resolver",
                "checkpoint": "external",
                "path": "Cargo.toml",
                "patterns": ['resolver = "3"'],
                "context_before": 0,
                "context_after": 0,
                "required": True,
            }
        ]
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
        evidence = collector.collect(self.spec_path)
        self.assertEqual(evidence["queries"][0]["repository"], collector.normalize_home(str(external)))

    def test_line_and_source_matches_share_lf_anchors_and_original_hashes(self) -> None:
        source = self.repository / "src" / "policy.rs"
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        for content in (b"alpha\nTARGET\n", b"alpha\r\nTARGET\r\n", b"alpha\rbravo\nTARGET\n"):
            for mode in ("line", "source"):
                with self.subTest(content=content, mode=mode):
                    source.write_bytes(content)
                    spec["queries"] = [{
                        "id": "target", "checkpoint": "current", "path": "src/policy.rs",
                        "patterns": ["TARGET"], "match_mode": mode,
                        "context_before": 0, "context_after": 0,
                    }]
                    self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
                    query = collector.collect(self.spec_path)["queries"][0]
                    self.assertEqual(query["captures"][0]["line_start"], 2)
                    self.assertEqual(query["snippets"][0]["lines"], [{"number": 2, "text": "TARGET"}])
                    self.assertEqual(query["source_sha256"], hashlib.sha256(content).hexdigest())

    def test_scoped_capture_preserves_bare_cr_and_an_unterminated_final_line(self) -> None:
        source = self.repository / "src" / "policy.rs"
        content = b"prefix\nalpha\rbravo\nTARGET"
        source.write_bytes(content)
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        spec["queries"] = [{
            "id": "target", "checkpoint": "current", "path": "src/policy.rs",
            "scope_start_pattern": "alpha", "patterns": ["bravo", "TARGET"],
            "match_mode": "source", "context_before": 0, "context_after": 0,
        }]
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
        query = collector.collect(self.spec_path)["queries"][0]
        self.assertEqual([capture["line_start"] for capture in query["captures"]], [2, 3])
        self.assertEqual(query["snippets"][0]["lines"], [
            {"number": 2, "text": "alpha\rbravo"}, {"number": 3, "text": "TARGET"},
        ])
        self.assertEqual(query["scope"]["line_start"], 2)
        self.assertEqual(query["source_sha256"], hashlib.sha256(content).hexdigest())


class RustCallInventoryTests(unittest.TestCase):
    def test_collects_owner_and_identity_arguments_without_matching_fragments_or_definitions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="rust-call-inventory-") as temporary:
            root = Path(temporary)
            source = root / "jobs.rs"
            source.write_text(
                '''fn patch_one() {
    replace_item_fn_if_needed(path, operation, syntax, "first", "reason", "done", r#"fn first() { nested(1, 2); }"#);
    let _fragment = "replace_item_fn_if_needed(path, operation, syntax, \\"wrong\\", reason, marker, replacement)";
}

fn patch_two() {
    // replace_item_fn_if_needed(path, operation, syntax, "wrong", reason, marker, replacement);
    replace_trait_impl_method_if_needed(&context(a, b), "Trait", "Type", "method", "reason", "done", replacement);
}

fn replace_item_fn_if_needed() {}

#[cfg(test)]
mod tests {
    fn patch_test() { replace_item_fn_if_needed(path, operation, syntax, "test", reason, marker, replacement); }
}
''',
                encoding="utf-8",
            )
            spec = root / "spec.json"
            spec.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": str(source),
                        "scope_end_pattern": "(?m)^#\\[cfg\\(test\\)\\]",
                        "owner_pattern": "(?m)^fn (?P<owner>patch_[a-z0-9_]+)\\s*\\(",
                        "calls": [
                            {
                                "callee": "replace_item_fn_if_needed",
                                "identity_args": [3],
                                "identity_labels": ["function"],
                            },
                            {
                                "callee": "replace_trait_impl_method_if_needed",
                                "identity_args": [1, 2, 3],
                                "identity_labels": ["trait", "self_type", "method"],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            inventory = call_inventory.collect(spec)
            self.assertEqual(inventory["call_count"], 2)
            self.assertEqual(inventory["owner_count"], 2)
            self.assertEqual(inventory["calls"][0]["owner"], "patch_one")
            self.assertEqual(inventory["calls"][0]["identity"], {"function": '"first"'})
            self.assertEqual(inventory["calls"][0]["site_key"], "patch_one::function=first")
            self.assertEqual(
                inventory["calls"][1]["identity"],
                {"trait": '"Trait"', "self_type": '"Type"', "method": '"method"'},
            )
            self.assertEqual(
                inventory["calls"][1]["site_key"],
                "patch_two::trait=Trait;self_type=Type;method=method",
            )
            markdown = call_inventory.render_markdown(inventory)
            self.assertIn("`patch_one`", markdown)
            self.assertIn("`patch_one::function=first`", markdown)
            self.assertNotIn("wrong", markdown)

    def test_rejects_call_after_owner_body_instead_of_using_preceding_declaration(self) -> None:
        with tempfile.TemporaryDirectory(prefix="rust-call-containment-") as temporary:
            root = Path(temporary)
            source = root / "jobs.rs"
            source.write_text(
                '''fn patch_one() {
    retained();
}

fn unrelated() {
    replace_item_fn_if_needed(path, operation, syntax, "outside", reason, marker, replacement);
}
''',
                encoding="utf-8",
            )
            spec = root / "spec.json"
            spec.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": str(source),
                        "owner_pattern": "(?m)^fn (?P<owner>patch_[a-z0-9_]+)\\s*\\(",
                        "calls": [
                            {
                                "callee": "replace_item_fn_if_needed",
                                "identity_args": [3],
                                "identity_labels": ["function"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(call_inventory.InventoryError, "not contained by a configured owner body"):
                call_inventory.collect(spec)

    def test_cli_rejects_unsupported_or_ambiguous_inventory_without_outputs(self) -> None:
        cases = [
            ('fn patch_one() { helper::<u8, u16>("target"); }', [0], ["selector"], "unsupported generic invocation"),
            ('fn patch_one() { helper(make::<u8, u16>(), "target"); }', [1], ["selector"], "unsupported generic syntax"),
            ('fn patch_one() { helper :: /* gap */ <u8>("target"); }', [0], ["selector"], "unsupported generic invocation"),
            ('unsafe extern "C" {\nfn patch_decl();\n}\nfn unrelated() { helper("outside"); }', [0], ["selector"], "declaration boundary"),
            ('fn patch_one() { helper("first", "second"); }', [0, 1], ["selector", "selector"], "duplicate identity label"),
        ]
        for content, indices, labels, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic, content=content):
                with tempfile.TemporaryDirectory(prefix="rust-inventory-rejection-") as temporary:
                    root = Path(temporary)
                    (root / "calls.rs").write_text(content, encoding="utf-8")
                    spec = root / "spec.json"
                    spec.write_text(json.dumps({
                        "schema_version": 1, "source": "calls.rs",
                        "owner_pattern": r"(?m)^fn (?P<owner>patch_[a-z0-9_]+)\s*\(",
                        "calls": [{"callee": "helper", "identity_args": indices, "identity_labels": labels}],
                    }), encoding="utf-8")
                    output_json, output_markdown = root / "inventory.json", root / "inventory.md"
                    result = subprocess.run([
                        sys.executable, "-B", str(SCRIPT_DIRECTORY / "collect_rust_call_inventory.py"),
                        "--spec", str(spec), "--output-json", str(output_json), "--output-markdown", str(output_markdown),
                    ], capture_output=True, text=True, check=False)
                    self.assertEqual(result.returncode, 1, result.stderr)
                    self.assertEqual(result.stdout, "")
                    self.assertIn(diagnostic, result.stderr)
                    self.assertFalse(output_json.exists())
                    self.assertFalse(output_markdown.exists())

    def test_preserves_array_return_types_and_unrelated_generic_syntax(self) -> None:
        with tempfile.TemporaryDirectory(prefix="rust-inventory-supported-") as temporary:
            root = Path(temporary)
            (root / "calls.rs").write_text('''fn patch_one() -> [u8; 2] {
    unrelated::<u8, u16>();
    helper("::<literal>");
    [0, 0]
}
''', encoding="utf-8")
            spec = root / "spec.json"
            spec.write_text(json.dumps({
                "schema_version": 1, "source": "calls.rs",
                "owner_pattern": r"(?m)^fn (?P<owner>patch_[a-z0-9_]+)\s*\(",
                "calls": [{"callee": "helper", "identity_args": [0], "identity_labels": ["selector"]}],
            }), encoding="utf-8")
            inventory = call_inventory.collect(spec)
            self.assertEqual(inventory["call_count"], 1)
            self.assertEqual(inventory["calls"][0]["owner"], "patch_one")
            self.assertEqual(inventory["calls"][0]["identity"], {"selector": '"::<literal>"'})


class VerdictPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = {
            "schema_version": 1,
            "require_unwrapped_prose": True,
            "forbidden_phrases": ["build an explicit review table"],
            "findings": [
                {
                    "id": "R1",
                    "required_sections": [
                        "Verdict",
                        "Historical and current evidence",
                        "Completed operation disposition",
                        "Actionable remediation",
                        "Required evidence",
                        "Remediation verdict",
                    ],
                    "required_evidence_queries": ["r1-current"],
                    "required_strings": ["`remove`"],
                    "minimum_source_locators": 1,
                    "minimum_verdict_units": 1,
                }
            ],
        }
        self.evidence_queries = {"r1-current"}

    def test_accepts_decision_ready_unwrapped_packet(self) -> None:
        packet = """# Packet

## Finding `R1`: ownership drift

### Verdict

Confirmed regression with a concrete `remove` disposition.

### Historical and current evidence

Evidence record `r1-current` captures `current:src/policy.rs:1-4`.

### Completed operation disposition

| Operation | Decision | Exact action |
|---|---|---|
| Generic policy | `remove` | Delete the generic owner and retain the narrow seam. |

### Actionable remediation

1. Delete the named generic operation and retain the named narrow operation.

### Required evidence

- The narrow operation remains active and unrelated source is unchanged.

### Remediation verdict

#### `R1-A` Remove the generic owner

**Evidence:** `r1-current` and `current:src/policy.rs:1-4`.

**Change:** Delete the generic operation and retain the narrow seam.

**Approval means:** Implement exactly this removal and preservation boundary.

**Rejection means:** Retain current ownership and do not perform this remediation unit.

**User verdict:** `approve / reject / question`

**User comment:** Add any qualification after selecting a verdict.
"""
        self.assertEqual(validator.validate(packet, self.contract, self.evidence_queries), [])
    def test_rejects_hardwrap_placeholder_deferral_and_incomplete_unit(self) -> None:
        packet = """## Finding `R1`: ownership drift

### Verdict

This paragraph is manually
wrapped and remains TBD.

### Historical and current evidence

Evidence record `r1-current` captures no locator.

### Completed operation disposition

Build an explicit review table.

### Actionable remediation

1. Classify ____________________________.

### Required evidence

Missing.

### Remediation verdict

#### `R1-A` Unknown

**Evidence:** Unknown.
"""
        errors = validator.validate(packet, self.contract, self.evidence_queries)
        self.assertTrue(any("manual prose wrapping" in error for error in errors))
        self.assertTrue(any("unresolved placeholder" in error for error in errors))
        self.assertTrue(any("forbidden deferral" in error for error in errors))
        self.assertTrue(any("source locators" in error for error in errors))
        self.assertTrue(any("missing label" in error for error in errors))

    def test_rejects_uncontracted_finding_and_its_placeholder(self) -> None:
        packet = """## Finding `R1`: ownership drift

### Verdict

Confirmed regression with a concrete `remove` disposition.

### Historical and current evidence

Evidence record `r1-current` captures `current:src/policy.rs:1-4`.

### Completed operation disposition

| Operation | Decision | Exact action |
|---|---|---|
| Generic policy | `remove` | Delete the generic owner and retain the narrow seam. |

### Actionable remediation

1. Delete the named generic operation and retain the named narrow operation.

### Required evidence

- The narrow operation remains active and unrelated source is unchanged.

### Remediation verdict

#### `R1-A` Remove the generic owner

**Evidence:** `r1-current` and `current:src/policy.rs:1-4`.

**Change:** Delete the generic operation and retain the narrow seam.

**Approval means:** Implement exactly this removal and preservation boundary.

**Rejection means:** Retain current ownership and do not perform this remediation unit.

**User verdict:** `approve / reject / question`

**User comment:** Add any qualification after selecting a verdict.

## Finding `R2`: separate unfinished audit

### Verdict

This uncontracted finding remains ____________________________.
"""
        errors = validator.validate(packet, self.contract, self.evidence_queries)
        self.assertTrue(any("uncontracted finding heading: R2" in error for error in errors))
        self.assertTrue(any("finding R2 contains an unresolved placeholder" in error for error in errors))

    def test_rejects_blank_verdict_unit_fields(self) -> None:
        contract = {
            "schema_version": 1,
            "require_unwrapped_prose": True,
            "forbidden_phrases": [],
            "findings": [
                {
                    "id": "R1",
                    "required_sections": [],
                    "required_evidence_queries": [],
                    "required_strings": [],
                    "minimum_source_locators": 0,
                    "minimum_verdict_units": 1,
                }
            ],
        }
        packet = """## Finding `R1`: blank verdict field

#### `R1-A` Decide

**Evidence:** Complete evidence.

**Change:** Apply the named change.

**Approval means:** Approve the named change.

**Rejection means:** Retain the current behavior.

**User verdict:** `approve / reject / question`

**User comment:**
"""
        errors = validator.validate(packet, contract, {})
        self.assertTrue(any("blank field: User comment" in error for error in errors))

    def test_pins_evidence_inventory_counts(self) -> None:
        contract = {
            "schema_version": 1,
            "require_unwrapped_prose": True,
            "forbidden_phrases": [],
            "findings": [
                {
                    "id": "R1",
                    "required_sections": [],
                    "required_evidence_queries": [],
                    "required_strings": [],
                    "minimum_source_locators": 0,
                    "minimum_verdict_units": 0,
                    "evidence_assertions": [
                        {
                            "query_id": "r1-current",
                            "match_count": 3,
                            "capture_count": 3,
                            "pattern_capture_counts": {"0": 2, "1": 1},
                        }
                    ],
                }
            ],
        }
        evidence = {
            "r1-current": {
                "id": "r1-current",
                "match_count": 3,
                "captures": [
                    {"pattern_index": 0},
                    {"pattern_index": 0},
                    {"pattern_index": 1},
                ],
            }
        }
        packet = "## Finding `R1`: source inventory\n"
        self.assertEqual(validator.validate(packet, contract, evidence), [])
        evidence["r1-current"]["match_count"] = 4
        errors = validator.validate(packet, contract, evidence)
        self.assertTrue(any("match_count 4" in error for error in errors))

    def test_requires_every_rust_call_site_key_in_the_finding(self) -> None:
        contract = {
            "schema_version": 1,
            "require_unwrapped_prose": True,
            "forbidden_phrases": [],
            "findings": [
                {
                    "id": "R5",
                    "required_sections": [],
                    "required_evidence_queries": [],
                    "required_strings": [],
                    "minimum_source_locators": 0,
                    "minimum_verdict_units": 0,
                    "rust_call_inventory": {
                        "source": "~/work/jobs.rs",
                        "call_count": 1,
                        "owner_count": 1,
                        "require_site_keys": True,
                    },
                }
            ],
        }
        inventory = {
            "schema_version": 1,
            "source": "~/work/jobs.rs",
            "call_count": 1,
            "owner_count": 1,
            "calls": [
                {
                    "owner": "patch_one",
                    "site_key": "patch_one::function=first",
                }
            ],
        }
        packet = "## Finding `R5`: whole-item review\n\n`patch_one::function=first`\n"
        self.assertEqual(validator.validate(packet, contract, {}, inventory), [])
        errors = validator.validate("## Finding `R5`: whole-item review\n", contract, {}, inventory)
        self.assertTrue(any("does not disposition Rust call site" in error for error in errors))


class FencedPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = {
            "schema_version": 1,
            "forbidden_phrases": ["build an explicit review table"],
            "findings": [{
                "id": "R1", "required_sections": ["Verdict"],
                "required_evidence_queries": ["q1"], "minimum_source_locators": 1,
                "minimum_verdict_units": 1,
            }],
        }
        self.packet = """## Finding `R1`: selected ownership

### Verdict

Keep the selected owner; `q1` captures `current:src/owner.rs:1-4`.

#### `R1-A` Keep the owner

**Evidence:** `q1` and `current:src/owner.rs:1-4`.

**Change:** Retain the named owner.

**Approval means:** Retain the named ownership boundary.

**Rejection means:** Reconsider the stated ownership choice.

**User verdict:** `approve / reject / question`

**User comment:** Add any qualification.
"""

    def test_fenced_examples_do_not_supply_findings_or_verdict_units(self) -> None:
        self.assertEqual(validator.validate(self.packet, self.contract, {"q1"}), [])
        for opening, closing in (("```", "```"), ("````", "`````"), ("~~~", "~~~~")):
            with self.subTest(opening=opening):
                example = f"{opening}markdown\n{self.packet}{closing}\n"
                errors = validator.validate(example, self.contract, {"q1"})
                self.assertIn("missing finding heading: R1", errors)
                prefix, unit = self.packet.split("####", maxsplit=1)
                example_unit = f"{prefix}{opening}markdown\n####{unit}{closing}\n"
                errors = validator.validate(example_unit, self.contract, {"q1"})
                self.assertIn("finding R1 has 0 verdict units; requires 1", errors)

    def test_fenced_source_words_and_nested_shorter_fences_are_not_decisions(self) -> None:
        for opening, body, closing in (
            ("```rust", 'const LABEL: &str = "TBD";', "```"),
            ("~~~text", "TODO: build an explicit review table\n## Finding `R2`: example", "~~~~"),
            ("````text", "```\nTBD\n#### `R2-A` example", "````"),
            ("~~~text", "```\nTBD", "~~~"),
        ):
            with self.subTest(opening=opening, body=body):
                packet = f"{self.packet}\n{opening}\n{body}\n{closing}\n"
                self.assertEqual(validator.validate(packet, self.contract, {"q1"}), [])
        errors = validator.validate(self.packet + "\nTBD\n", self.contract, {"q1"})
        self.assertIn("finding R1 contains an unresolved placeholder marker", errors)
        errors = validator.validate(self.packet + "\nbuild an explicit review table\n", self.contract, {"q1"})
        self.assertTrue(any("forbidden deferral" in error for error in errors))

    def test_fenced_sections_citations_and_field_values_do_not_fill_requirements(self) -> None:
        cases = [
            (self.packet.replace("### Verdict", "```markdown\n### Verdict\n```"), "missing subsection: Verdict"),
            (self.packet.replace("`q1`", "the source query") + "\n```text\n`q1`\n```\n", "does not cite evidence query: q1"),
            (self.packet.replace("**Change:** Retain the named owner.", "**Change:**\n\n```text\nRetain the named owner.\n```"), "blank field: Change"),
        ]
        for packet, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                errors = validator.validate(packet, self.contract, {"q1"})
                self.assertTrue(any(diagnostic in error for error in errors), errors)

    def test_cli_preserves_passed_and_failed_packet_results(self) -> None:
        with tempfile.TemporaryDirectory(prefix="packet-fence-cli-") as temporary:
            root = Path(temporary)
            packet, contract, evidence = root / "packet.md", root / "contract.json", root / "evidence.json"
            contract.write_text(json.dumps(self.contract), encoding="utf-8")
            evidence.write_text(json.dumps({"schema_version": 1, "queries": [{"id": "q1"}]}), encoding="utf-8")
            for content, expected_exit, expected_status in (
                (self.packet + '\n```rust\nconst LABEL: &str = "TBD";\n```\n', 0, "passed"),
                ("```markdown\n" + self.packet + "```\n", 1, "failed"),
            ):
                with self.subTest(expected_status=expected_status):
                    packet.write_text(content, encoding="utf-8")
                    result = subprocess.run([
                        sys.executable, "-B", str(SCRIPT_DIRECTORY / "validate_verdict_packet.py"),
                        "--packet", str(packet), "--contract", str(contract), "--evidence-json", str(evidence),
                    ], capture_output=True, text=True, check=False)
                    self.assertEqual(result.returncode, expected_exit, result.stderr)
                    report = json.loads(result.stdout if expected_exit == 0 else result.stderr)
                    self.assertEqual(report["status"], expected_status)


class OperationalDiagnosticTests(unittest.TestCase):
    def test_inventory_read_and_write_failures_normalize_home_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="inventory-diagnostic-") as temporary:
            root = Path(temporary)
            spec = root / "spec.json"
            source = root / "calls.rs"
            source.write_text('fn patch_one() { helper("target"); }', encoding="utf-8")
            blocked = root / "blocked"
            blocked.write_text("preserve this file", encoding="utf-8")
            for source_name, output, expected_path in (
                ("missing.rs", root / "inventory.json", "~/missing.rs"),
                ("calls.rs", blocked / "inventory.json", "~/blocked"),
            ):
                with self.subTest(source_name=source_name):
                    spec.write_text(json.dumps({
                        "schema_version": 1, "source": source_name,
                        "owner_pattern": r"(?m)^fn (?P<owner>patch_[a-z0-9_]+)\s*\(",
                        "calls": [{"callee": "helper", "identity_args": [0], "identity_labels": ["selector"]}],
                    }), encoding="utf-8")
                    stdout, stderr = io.StringIO(), io.StringIO()
                    with mock.patch.object(Path, "home", return_value=root), mock.patch.object(sys, "argv", [
                        "collect_rust_call_inventory.py", "--spec", str(spec), "--output-json", str(output),
                        "--output-markdown", str(root / "inventory.md"),
                    ]), redirect_stdout(stdout), redirect_stderr(stderr):
                        exit_status = call_inventory.main()
                    self.assertEqual(exit_status, 1)
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertIn(expected_path, stderr.getvalue())
                    self.assertNotIn(str(root), stderr.getvalue())
                    self.assertNotIn("Traceback", stderr.getvalue())
                    self.assertEqual(blocked.read_text(encoding="utf-8"), "preserve this file")

    def test_packet_invalid_input_preserves_structure_and_normalizes_home_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="packet-diagnostic-") as temporary:
            root = Path(temporary)
            stdout, stderr = io.StringIO(), io.StringIO()
            with mock.patch.object(Path, "home", return_value=root), mock.patch.object(sys, "argv", [
                "validate_verdict_packet.py", "--packet", str(root / "missing.md"),
                "--contract", str(root / "contract.json"), "--evidence-json", str(root / "evidence.json"),
            ]), redirect_stdout(stdout), redirect_stderr(stderr):
                exit_status = validator.main()
            self.assertEqual(exit_status, 2)
            self.assertEqual(stdout.getvalue(), "")
            report = json.loads(stderr.getvalue())
            self.assertEqual(report["status"], "invalid-input")
            self.assertEqual(len(report["errors"]), 1)
            self.assertIn("~/missing.md", report["errors"][0])
            self.assertNotIn(str(root), stderr.getvalue())


class MarkdownStyleTests(unittest.TestCase):
    def test_authored_markdown_does_not_manually_wrap_prose(self) -> None:
        paths = [
            SKILL_ROOT / "SKILL.md",
            SKILL_ROOT / "references" / "source-evidence-spec.md",
            SKILL_ROOT / "references" / "rust-call-inventory-spec.md",
        ]
        for path in paths:
            with self.subTest(path=path):
                lines = path.read_text(encoding="utf-8").splitlines()
                self.assertEqual(validator.hardwrapped_lines(lines), [])

    def test_packet_is_decision_evidence_not_repository_mutation_authority(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("decision evidence", skill)
        self.assertIn("never repository-mutation authority", skill)
        self.assertIn("do not use this skill", skill.lower())


if __name__ == "__main__":
    unittest.main()
