#!/usr/bin/env python3
"""Behavior tests for the architectural-regression audit scripts."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


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
