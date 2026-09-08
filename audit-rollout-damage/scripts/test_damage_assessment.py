#!/usr/bin/env python3
"""Direct integration tests for the reusable rollout damage scripts."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

import damage_common
import discover_edit_candidates
import extract_rollout_context
import index_rollout_tools
import render_damage_assessment


SCRIPTS = Path(__file__).resolve().parent


def write_json(path: Path, value: object) -> None:
    """Write deterministic fixture JSON."""
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def hash_file(path: Path) -> str:
    """Hash one fixture file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_evidence(root: Path) -> Path:
    """Write a complete report fixture for the snapshot and range regressions."""
    path = root / "facts.json"
    write_json(path, {"records": [
        {"path": "small.rs", "added": 1, "removed": 0, "patch_lines": ["+small"]},
        {"path": "middle.rs", "added": 3, "removed": 2, "patch_lines": ["-old middle", "+new middle"]},
        {"path": "another-large.rs", "added": 9, "removed": 4, "patch_lines": ["-old another", "+new another"]},
        {"path": "large.rs", "added": 9, "removed": 4, "patch_lines": ["-old large", "+new large"]},
    ]})
    return path


@contextmanager
def replace_after_read(replacements: dict[Path, bytes]) -> Iterator[None]:
    """Replace owned inputs after their first read to expose mixed snapshots."""
    pending = dict(replacements)
    original_bytes = Path.read_bytes
    original_text = Path.read_text

    def replace(path: Path) -> None:
        replacement = pending.pop(path, None)
        if replacement is not None:
            path.write_bytes(replacement)

    def read_bytes(path: Path) -> bytes:
        data = original_bytes(path)
        replace(path)
        return data

    def read_text(path: Path, *args, **kwargs) -> str:
        text = original_text(path, *args, **kwargs)
        replace(path)
        return text

    with mock.patch.object(Path, "read_bytes", read_bytes), mock.patch.object(Path, "read_text", read_text):
        yield


def reference(input_id: str, locator: str) -> dict[str, str]:
    """Create one fixture evidence reference."""
    return {"input": input_id, "locator": locator}


def cited(text: str, locator: str = "records") -> dict[str, object]:
    """Create one fixture statement with typed evidence."""
    return {"text": text, "evidence_refs": [reference("facts", locator)]}


def dossier(identifier: str, identity: str) -> dict[str, object]:
    """Create one complete fixture representative decision dossier."""
    locator = f"records[path={identity}]"
    return {
        "record_id": identifier,
        "title": f"Decision account for {identity}",
        "verbatim_exhibits": [
            {
                "title": f"Exact normalized change for {identity}",
                "language": "diff",
                "scope": "complete_change",
                "effect_state": "landed",
                "source": {
                    "select": {"input": "facts", "path": ["records"], "where": {"path": identity}},
                    "extract_path": [0, "patch_lines"],
                },
                "interpretation": cited(
                    f"The exact patch changes the fixture record for {identity}.", locator
                ),
                "evidence_refs": [reference("facts", locator)],
            }
        ],
        "summary": cited(f"This dossier explains why {identity} matters.", locator),
        "prior_state": cited(f"Before the change, {identity} had the fixture baseline behavior.", locator),
        "change": cited(f"The selected operation changed {identity} in the measured way.", locator),
        "trace_context": [cited("The fixture trace identifies the request, explanation, and effect.", locator)],
        "stated_rationale": cited("The fixture rationale was to exercise generic reporting.", locator),
        "authority_assessment": {
            "status": "indeterminate",
            "assessment": cited("The fixture does not establish real-world authority.", locator),
        },
        "behavioral_effects": [cited("The record changes the fixture output used by the report.", locator)],
        "causal_dependencies": [cited("The renderer consumes this frozen evidence record.", locator)],
        "keep_consequences": [cited("Keeping it retains the fixture's selected behavior.", locator)],
        "reverse_consequences": [cited("Reversing it restores the fixture baseline.", locator)],
        "recommended_disposition": {
            "action": cited("Review the fixture record before any hypothetical repair.", locator),
            "reasons": [cited("The fixture intentionally carries no external authority.", locator)],
            "risks": [cited("Treating it as a real incident would overstate the evidence.", locator)],
        },
        "confidence": {
            "level": "high",
            "basis": cited("The fixture record and expected rendering are deterministic.", locator),
        },
        "unknowns": [],
    }


def record(identifier: str, identity: str, path: str) -> dict[str, object]:
    """Create one measured fixture record."""
    return {
        "id": identifier,
        "identity": identity,
        "description": f"Measured {identity} from evidence.",
        "landed_state": "landed",
        "candidate_state": "review_only",
        "evidence_refs": [reference("facts", f"records[path={path}]")],
        "measurement": {
            "select": {"input": "facts", "path": ["records"], "where": {"path": path}},
            "operation": "sum_fields",
            "fields": ["added", "removed"],
        },
    }


def manifest(evidence: Path, evidence_hash: str) -> dict[str, object]:
    """Create a complete reusable fixture manifest."""
    return {
        "schema_version": 4,
        "evidence_inputs": [
            {
                "id": "facts",
                "path": str(evidence),
                "sha256": evidence_hash,
                "format": "json",
                "role": "Fixture change facts.",
            }
        ],
        "qualification_levels": [
            {
                "id": "Q1",
                "title": "Fixture level",
                "definition": "Exact fixture candidates.",
                "metric": {
                    "name": "Recorded churn",
                    "unit": "lines",
                    "caveat": "Churn is not final net change.",
                },
                "automatic_action": "None.",
                "records": [
                    record("small", "small.rs", "small.rs"),
                    record("middle", "middle.rs", "middle.rs"),
                    record("another-large", "another-large.rs", "another-large.rs"),
                    record("large", "large.rs", "large.rs"),
                ],
                "representative_assessments": [
                    dossier("small", "small.rs"),
                    dossier("another-large", "another-large.rs"),
                    dossier("middle", "middle.rs"),
                ],
            }
        ],
        "report": {
            "title": "Fixture damage assessment",
            "scope": ["Cover the selected fixture only."],
            "conclusion": ["The fixture is deterministic."],
            "authority": ["The report does not authorize remediation."],
            "headline_facts": [
                {
                    "id": "record-count",
                    "label": "Evidence records",
                    "unit": "records",
                    "description": "Records in the fixture input.",
                    "evidence_refs": [reference("facts", "records")],
                    "measurement": {
                        "select": {"input": "facts", "path": ["records"]},
                        "operation": "count_records",
                    },
                }
            ],
            "terminology": [
                {
                    "term": "Inert candidate",
                    "definition": "A non-applying future-operation description.",
                    "not_equivalent_to": ["A harmless landed change."],
                    "examples": ["An exact prior-byte candidate that has not been applied."],
                }
            ],
            "measurement_notes": ["Sizes come from the frozen fixture input."],
            "qualitative_changes": [
                {
                    "id": "fixture",
                    "title": "Fixture behavior",
                    "summary": "The fixture exercises generic rendering.",
                    "impacts": ["It proves no incident path is required by the renderer."],
                    "examples": [
                        {
                            "identity": "middle.rs",
                            "description": "A cited qualitative example.",
                            "evidence_refs": [reference("facts", "records[path=middle.rs]")],
                        }
                    ],
                }
            ],
            "decision_evidence_packets": [
                {
                    "id": "fixture-files",
                    "title": "Fixture file changes",
                    "summary": "This packet makes every fixture change visible before a remediation verdict.",
                    "changes": [
                        {
                            "id": "fixture-patches",
                            "title": "Recorded fixture patches",
                            "artifacts": ["small.rs", "middle.rs", "another-large.rs", "large.rs"],
                            "what_changed": [
                                "Each fixture record carries its exact normalized patch lines."
                            ],
                            "why_it_matters": [
                                "A reviewer can see the bytes covered by the verdict without opening another file."
                            ],
                            "evidence_refs": [reference("facts", "records")],
                        }
                    ],
                    "trace_appendix": {
                        "title": "Complete fixture patch evidence",
                        "language": "diff",
                        "effect_state": "landed",
                        "description": "Every selected fixture patch is rendered exactly and labelled by path.",
                        "source": {
                            "select": {
                                "input": "facts",
                                "path": ["records"],
                                "where": {
                                    "path": {
                                        "in": ["small.rs", "middle.rs", "another-large.rs", "large.rs"]
                                    },
                                    "added": {"gte": 1},
                                },
                            },
                            "extract_each_path": ["patch_lines"],
                            "label_fields": ["path"],
                        },
                        "evidence_refs": [reference("facts", "records")],
                    },
                    "evidence_refs": [reference("facts", "records")],
                }
            ],
            "remediation_options": [
                {
                    "role": "aggressive",
                    "title": "Aggressive remediation",
                    "summary": "Prefer broad exact restoration.",
                    "actions": ["Restore exact candidates after authorization."],
                    "decision_units": [
                        {
                            "id": "fixture-files",
                            "title": "Fixture files",
                            "artifacts": ["small.rs", "middle.rs", "another-large.rs", "large.rs"],
                            "evidence_packet": "fixture-files",
                            "retain": [],
                            "remove_or_restore": ["Restore every fixture record to its recorded baseline."],
                            "requires_decision": [],
                            "approved_means": [
                                "Record aggressive fixture restoration as the selected future remediation."
                            ],
                            "rejected_means": [
                                "Do not use aggressive fixture restoration for this unit."
                            ],
                            "reason": "The aggressive fixture option treats the complete set uniformly.",
                            "evidence_refs": [reference("facts", "records")],
                        }
                    ],
                    "reasons": ["It minimizes tainted retention."],
                    "risks": ["It may discard independently valid work."],
                },
                {
                    "role": "conservative",
                    "title": "Conservative remediation",
                    "summary": "Adjudicate every statement.",
                    "actions": ["Review each record before any repair."],
                    "decision_units": [
                        {
                            "id": "fixture-files",
                            "title": "Fixture files",
                            "artifacts": ["small.rs", "middle.rs", "another-large.rs", "large.rs"],
                            "evidence_packet": "fixture-files",
                            "retain": ["Retain every current fixture byte during adjudication."],
                            "remove_or_restore": [],
                            "requires_decision": ["Decide each fixture record independently."],
                            "approved_means": [
                                "Record conservative fixture retention as the selected future remediation."
                            ],
                            "rejected_means": [
                                "Do not use conservative fixture retention for this unit."
                            ],
                            "reason": "The conservative fixture option defers every mutation.",
                            "evidence_refs": [reference("facts", "records")],
                        }
                    ],
                    "reasons": ["It maximizes preservation."],
                    "risks": ["It is slow and can retain tainted structure."],
                },
                {
                    "role": "recommended",
                    "title": "Recommended remediation",
                    "summary": "Combine exact and statement-level repair.",
                    "actions": ["Use exact candidates where authority is uniform."],
                    "decision_units": [
                        {
                            "id": "fixture-files",
                            "title": "Fixture files",
                            "artifacts": ["small.rs", "middle.rs", "another-large.rs", "large.rs"],
                            "evidence_packet": "fixture-files",
                            "retain": ["Retain records whose authority is independently established."],
                            "remove_or_restore": ["Restore records proven to belong only to the rejected wave."],
                            "requires_decision": ["Classify mixed-authority records before mutation."],
                            "approved_means": [
                                "Record the hybrid fixture boundary as the selected future remediation."
                            ],
                            "rejected_means": [
                                "Do not use the hybrid fixture boundary for this unit."
                            ],
                            "reason": "The recommended fixture option separates uniform from mixed authority.",
                            "evidence_refs": [reference("facts", "records")],
                        }
                    ],
                    "reasons": ["It balances confidence and preservation."],
                    "risks": ["It still requires user decisions."],
                },
            ],
            "recommendation": "recommended",
            "limits": ["The fixture is not product verification."],
        },
    }


class DamageAssessmentScriptsTest(unittest.TestCase):
    """Exercise the generic report and trace-navigation paths."""

    def test_renderer_computes_representatives_from_evidence(self) -> None:
        """Render statistics and real examples without incident-specific code."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "facts.json"
            write_json(
                evidence,
                {
                    "records": [
                        {"path": "small.rs", "added": 1, "removed": 0, "patch_lines": ["+small"]},
                        {"path": "middle.rs", "added": 3, "removed": 2, "patch_lines": ["-old middle", "+new middle"]},
                        {"path": "another-large.rs", "added": 9, "removed": 4, "patch_lines": ["-old another", "+new another"]},
                        {"path": "large.rs", "added": 9, "removed": 4, "patch_lines": ["-old large", "+new large"]},
                    ]
                },
            )
            manifest_path = root / "manifest.json"
            write_json(manifest_path, manifest(evidence, hash_file(evidence)))
            markdown = root / "report.md"
            derived = root / "report.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "render_damage_assessment.py"),
                    "--manifest",
                    str(manifest_path),
                    "--output-markdown",
                    str(markdown),
                    "--output-json",
                    str(derived),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(derived.read_text(encoding="utf-8"))
            statistics = result["qualification_levels"][0]["statistics"]
            self.assertEqual(statistics["count"], 4)
            self.assertEqual(statistics["total"], 32)
            self.assertEqual(statistics["mean"], 8.0)
            self.assertEqual(statistics["median"], 9.0)
            self.assertEqual(statistics["representatives"]["smallest"]["selected"]["identity"], "small.rs")
            self.assertEqual(statistics["representatives"]["largest"]["selected"]["identity"], "another-large.rs")
            self.assertEqual(statistics["representatives"]["largest"]["tie_count"], 2)
            markdown_text = markdown.read_text(encoding="utf-8")
            self.assertIn("Recommended remediation — selected recommendation", markdown_text)
            self.assertIn("Qualitative decision dossiers", markdown_text)
            self.assertEqual(markdown_text.count("##### `another-large`"), 1)
            self.assertIn("Statistical roles: `largest`, `median`", markdown_text)
            self.assertIn("**Verbatim change exhibit — Exact normalized change for another-large.rs.**", markdown_text)
            self.assertIn("-old another\n+new another", markdown_text)
            self.assertIn("#### `fixture-files` — Fixture files", markdown_text)
            self.assertIn("## Remediation decision evidence", markdown_text)
            self.assertIn("### `fixture-files` — Fixture file changes", markdown_text)
            self.assertIn("Complete fixture patch evidence — 4 exact fragment(s)", markdown_text)
            self.assertIn(
                "Decision evidence: [view the complete `fixture-files` packet](#decision-evidence-fixture-files).",
                markdown_text,
            )
            self.assertIn("Decision requested:", markdown_text)
            self.assertIn("If you enter `Approved`:", markdown_text)
            self.assertIn("If you enter `Reject`:", markdown_text)
            self.assertEqual(
                markdown_text.count("**User Verdict:** `[Approved / Reject / Question/Comment]`"),
                3,
            )
            self.assertEqual(markdown_text.count("**User Question/Comment:** `[Type here]`"), 3)

    def test_renderer_resolves_selected_verbatim_lines_and_discloses_omissions(self) -> None:
        """Render only the declared exact slice and explain what was not shown."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "facts.json"
            write_json(
                evidence,
                {
                    "records": [
                        {"path": "small.rs", "added": 1, "removed": 0, "patch_lines": ["+small"]},
                        {"path": "middle.rs", "added": 3, "removed": 2, "patch_lines": ["context", "-old middle", "+new middle", "tail"]},
                        {"path": "another-large.rs", "added": 9, "removed": 4, "patch_lines": ["-old another", "+new another"]},
                        {"path": "large.rs", "added": 9, "removed": 4, "patch_lines": ["-old large", "+new large"]},
                    ]
                },
            )
            value = manifest(evidence, hash_file(evidence))
            exhibit = value["qualification_levels"][0]["representative_assessments"][2]["verbatim_exhibits"][0]
            exhibit["scope"] = "selected_excerpt"
            exhibit["source"]["start_line"] = 2
            exhibit["source"]["line_count"] = 2
            exhibit["omitted"] = "The context and tail lines are outside this selected excerpt."
            manifest_path = root / "manifest.json"
            write_json(manifest_path, value)
            markdown = root / "report.md"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "render_damage_assessment.py"),
                    "--manifest",
                    str(manifest_path),
                    "--output-markdown",
                    str(markdown),
                    "--output-json",
                    str(root / "report.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            text = markdown.read_text(encoding="utf-8")
            middle_dossier = text.split("##### `middle`", 1)[1].split("**Decision summary.**", 1)[0]
            self.assertIn("-old middle\n+new middle", middle_dossier)
            self.assertNotIn("context\n-old middle", middle_dossier)
            self.assertIn("The context and tail lines are outside this selected excerpt.", middle_dossier)

    def test_renderer_rejects_selected_excerpt_without_omission_inventory(self) -> None:
        """Refuse a partial quotation that does not say what it leaves out."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "facts.json"
            write_json(
                evidence,
                {
                    "records": [
                        {"path": "small.rs", "added": 1, "removed": 0, "patch_lines": ["+small"]},
                        {"path": "middle.rs", "added": 3, "removed": 2, "patch_lines": ["-old middle", "+new middle"]},
                        {"path": "another-large.rs", "added": 9, "removed": 4, "patch_lines": ["-old another", "+new another"]},
                        {"path": "large.rs", "added": 9, "removed": 4, "patch_lines": ["-old large", "+new large"]},
                    ]
                },
            )
            value = manifest(evidence, hash_file(evidence))
            value["qualification_levels"][0]["representative_assessments"][0]["verbatim_exhibits"][0]["scope"] = "selected_excerpt"
            manifest_path = root / "manifest.json"
            write_json(manifest_path, value)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "render_damage_assessment.py"),
                    "--manifest",
                    str(manifest_path),
                    "--output-markdown",
                    str(root / "report.md"),
                    "--output-json",
                    str(root / "report.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("omitted: required", completed.stderr)
            self.assertFalse((root / "report.md").exists())

    def test_renderer_rejects_out_of_range_verbatim_slice(self) -> None:
        """Fail closed when a manifest excerpt no longer resolves exactly."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "facts.json"
            write_json(
                evidence,
                {
                    "records": [
                        {"path": "small.rs", "added": 1, "removed": 0, "patch_lines": ["+small"]},
                        {"path": "middle.rs", "added": 3, "removed": 2, "patch_lines": ["-old middle", "+new middle"]},
                        {"path": "another-large.rs", "added": 9, "removed": 4, "patch_lines": ["-old another", "+new another"]},
                        {"path": "large.rs", "added": 9, "removed": 4, "patch_lines": ["-old large", "+new large"]},
                    ]
                },
            )
            value = manifest(evidence, hash_file(evidence))
            exhibit = value["qualification_levels"][0]["representative_assessments"][0]["verbatim_exhibits"][0]
            exhibit["scope"] = "selected_excerpt"
            exhibit["source"]["start_line"] = 2
            exhibit["source"]["line_count"] = 1
            exhibit["omitted"] = "The remaining lines are omitted."
            manifest_path = root / "manifest.json"
            write_json(manifest_path, value)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "render_damage_assessment.py"),
                    "--manifest",
                    str(manifest_path),
                    "--output-markdown",
                    str(root / "report.md"),
                    "--output-json",
                    str(root / "report.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("exceeds 1 available line(s)", completed.stderr)
            self.assertFalse((root / "report.md").exists())

    def test_renderer_rejects_missing_representative_dossier(self) -> None:
        """Refuse a quantitative-only report that omits a selected record's meaning."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "facts.json"
            write_json(
                evidence,
                {
                    "records": [
                        {"path": "small.rs", "added": 1, "removed": 0, "patch_lines": ["+small"]},
                        {"path": "middle.rs", "added": 3, "removed": 2, "patch_lines": ["-old middle", "+new middle"]},
                        {"path": "another-large.rs", "added": 9, "removed": 4, "patch_lines": ["-old another", "+new another"]},
                        {"path": "large.rs", "added": 9, "removed": 4, "patch_lines": ["-old large", "+new large"]},
                    ]
                },
            )
            value = manifest(evidence, hash_file(evidence))
            value["qualification_levels"][0]["representative_assessments"].pop()
            manifest_path = root / "manifest.json"
            write_json(manifest_path, value)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "render_damage_assessment.py"),
                    "--manifest",
                    str(manifest_path),
                    "--output-markdown",
                    str(root / "report.md"),
                    "--output-json",
                    str(root / "report.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("dossier mismatch", completed.stderr)
            self.assertFalse((root / "report.md").exists())

    def test_renderer_rejects_verdict_without_a_known_evidence_packet(self) -> None:
        """Refuse a verdict surface that cannot lead to its exact changes."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "facts.json"
            write_json(
                evidence,
                {
                    "records": [
                        {"path": "small.rs", "added": 1, "removed": 0, "patch_lines": ["+small"]},
                        {"path": "middle.rs", "added": 3, "removed": 2, "patch_lines": ["-old middle", "+new middle"]},
                        {"path": "another-large.rs", "added": 9, "removed": 4, "patch_lines": ["-old another", "+new another"]},
                        {"path": "large.rs", "added": 9, "removed": 4, "patch_lines": ["-old large", "+new large"]},
                    ]
                },
            )
            value = manifest(evidence, hash_file(evidence))
            value["report"]["remediation_options"][0]["decision_units"][0]["evidence_packet"] = "missing-packet"
            manifest_path = root / "manifest.json"
            write_json(manifest_path, value)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "render_damage_assessment.py"),
                    "--manifest",
                    str(manifest_path),
                    "--output-markdown",
                    str(root / "report.md"),
                    "--output-json",
                    str(root / "report.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("unknown packet 'missing-packet'", completed.stderr)
            self.assertFalse((root / "report.md").exists())

    def test_renderer_rejects_stale_evidence_hash(self) -> None:
        """Refuse to render after an evidence input changes."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "facts.json"
            write_json(evidence, {"records": []})
            manifest_path = root / "manifest.json"
            write_json(manifest_path, manifest(evidence, "0" * 64))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "render_damage_assessment.py"),
                    "--manifest",
                    str(manifest_path),
                    "--output-markdown",
                    str(root / "report.md"),
                    "--output-json",
                    str(root / "report.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("SHA-256 mismatch", completed.stderr)
            self.assertFalse((root / "report.md").exists())

    def test_reproducibility_runner_compares_two_fresh_runs(self) -> None:
        """Require byte-identical Markdown and JSON from frozen evidence."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "facts.json"
            write_json(
                evidence,
                {
                    "records": [
                        {"path": "small.rs", "added": 1, "removed": 0, "patch_lines": ["+small"]},
                        {"path": "middle.rs", "added": 3, "removed": 2, "patch_lines": ["-old middle", "+new middle"]},
                        {"path": "another-large.rs", "added": 9, "removed": 4, "patch_lines": ["-old another", "+new another"]},
                        {"path": "large.rs", "added": 9, "removed": 4, "patch_lines": ["-old large", "+new large"]},
                    ]
                },
            )
            manifest_path = root / "manifest.json"
            write_json(manifest_path, manifest(evidence, hash_file(evidence)))
            summary = root / "reproducibility.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "verify_damage_assessment.py"),
                    "--manifest",
                    str(manifest_path),
                    "--output-root",
                    str(root / "runs"),
                    "--output",
                    str(summary),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(summary.read_text(encoding="utf-8"))
            self.assertTrue(result["outputs_byte_identical"])

    def test_trace_index_and_candidate_discovery_handle_wrapped_patch(self) -> None:
        """Navigate one rollout and recover a JavaScript-wrapped patch call."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            repository.mkdir()
            session = root / "rollout.jsonl"
            wrapped = 'const patch = "*** Begin Patch\\n*** Add File: src/new.rs\\n+new\\n*** End Patch"; await tools.apply_patch(patch);'
            records = [
                {"type": "session_meta", "payload": {"id": "rollout-fixture"}},
                {
                    "type": "response_item",
                    "payload": {"type": "custom_tool_call", "id": "call-1", "name": "exec", "input": wrapped},
                },
                {
                    "type": "response_item",
                    "payload": {"type": "custom_tool_call_output", "call_id": "call-1", "output": "Done!"},
                },
            ]
            session.write_text("".join(json.dumps(item) + "\n" for item in records), encoding="utf-8")
            index = root / "index.json"
            indexed = subprocess.run(
                [sys.executable, str(SCRIPTS / "index_rollout_tools.py"), "--session", str(session), "--output", str(index)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(indexed.returncode, 0, indexed.stderr)
            candidates = root / "candidates.json"
            discovered = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "discover_edit_candidates.py"),
                    "--tool-index",
                    str(index),
                    "--repository",
                    str(repository),
                    "--output",
                    str(candidates),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(discovered.returncode, 0, discovered.stderr)
            result = json.loads(candidates.read_text(encoding="utf-8"))
            self.assertEqual(result["candidates"][0]["operations"], [{"operation": "add", "target": "src/new.rs"}])

    def test_candidate_discovery_parses_nested_exec_and_uses_exact_results(self) -> None:
        """Classify nested commands while leaving absent or conflicting status unknown."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            repository.mkdir()
            home_target = Path.home() / "nested-artifact"
            nested_input = {
                "cmd": f"touch {home_target}",
                "workdir": str(repository),
                "yield_time_ms": 1_000,
            }
            wrapped = f"const result = await tools.exec_command({json.dumps(nested_input)}); text(result.output);"
            calls = [
                ("call-nested", "exec", wrapped, {"exit_code": 0, "output": str(home_target)}),
                (
                    "call-failed",
                    "exec_command",
                    {"cmd": "touch failed", "workdir": str(repository)},
                    {"exit_code": 9},
                ),
                (
                    "call-unknown",
                    "exec_command",
                    {"cmd": "touch unknown", "workdir": str(repository)},
                    "Done!",
                ),
                (
                    "call-completed",
                    "exec_command",
                    {"cmd": "touch completed", "workdir": str(repository)},
                    "Done!",
                ),
                (
                    "call-conflict",
                    "exec_command",
                    {"cmd": "touch conflict", "workdir": str(repository)},
                    {"exit_code": 0, "isError": True},
                ),
            ]
            records: list[dict[str, object]] = [
                {"type": "session_meta", "payload": {"id": "rollout-exec-results"}}
            ]
            for call_id, name, tool_input, output in calls:
                output_payload: dict[str, object] = {
                    "type": "custom_tool_call_output",
                    "call_id": call_id,
                    "output": output,
                }
                if call_id in {"call-failed", "call-completed"}:
                    output_payload["status"] = "completed"
                records.extend(
                    [
                        {
                            "type": "response_item",
                            "payload": {
                                "type": "custom_tool_call",
                                "id": call_id,
                                "name": name,
                                "input": tool_input,
                            },
                        },
                        {
                            "type": "response_item",
                            "payload": output_payload,
                        },
                    ]
                )
            session = root / "rollout.jsonl"
            session.write_text("".join(json.dumps(item) + "\n" for item in records), encoding="utf-8")
            index = root / "index.json"
            indexed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "index_rollout_tools.py"),
                    "--session",
                    str(session),
                    "--output",
                    str(index),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(indexed.returncode, 0, indexed.stderr)
            candidates = root / "candidates.json"
            discovered = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "discover_edit_candidates.py"),
                    "--tool-index",
                    str(index),
                    "--repository",
                    str(repository),
                    "--output",
                    str(candidates),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(discovered.returncode, 0, discovered.stderr)
            indexed_text = index.read_text(encoding="utf-8")
            candidate_text = candidates.read_text(encoding="utf-8")
            expanded_home = str(Path.home().resolve(strict=False))
            self.assertNotIn(expanded_home, indexed_text)
            self.assertNotIn(expanded_home, candidate_text)
            self.assertIn("~/nested-artifact", indexed_text)
            result = json.loads(candidate_text)
            by_call = {item["call_id"]: item for item in result["candidates"]}
            self.assertEqual(by_call["call-nested"]["reported_success"], True)
            self.assertEqual(by_call["call-nested"]["nested_tool"], "exec_command")
            self.assertEqual(by_call["call-failed"]["reported_success"], False)
            self.assertIsNone(by_call["call-unknown"]["reported_success"])
            self.assertIsNone(by_call["call-completed"]["reported_success"])
            self.assertIsNone(by_call["call-conflict"]["reported_success"])

    def test_candidate_discovery_retains_unparsed_mutation_wrapper(self) -> None:
        """Emit unsupported evidence instead of dropping mutation-shaped JavaScript."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            repository.mkdir()
            source = (
                'await tools.exec_command({cmd: "touch marker", '
                f'workdir: "{repository}"}});'
            )
            records = [
                {"type": "session_meta", "payload": {"id": "rollout-unparsed-wrapper"}},
                {
                    "type": "response_item",
                    "payload": {
                        "type": "custom_tool_call",
                        "id": "call-unparsed",
                        "name": "exec",
                        "input": source,
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "custom_tool_call_output",
                        "call_id": "call-unparsed",
                        "output": "Done!",
                    },
                },
            ]
            session = root / "rollout.jsonl"
            session.write_text("".join(json.dumps(item) + "\n" for item in records), encoding="utf-8")
            index = root / "index.json"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "index_rollout_tools.py"),
                    "--session",
                    str(session),
                    "--output",
                    str(index),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            candidates = root / "candidates.json"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "discover_edit_candidates.py"),
                    "--tool-index",
                    str(index),
                    "--repository",
                    str(repository),
                    "--output",
                    str(candidates),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(candidates.read_text(encoding="utf-8"))
            self.assertEqual(result["candidates"], [])
            unsupported = result["unsupported_mutation_shaped_calls"]
            self.assertEqual(len(unsupported), 1)
            self.assertEqual(
                unsupported[0]["reason"],
                "mutation-shaped exec wrapper contains unparsed tools.exec_command input",
            )
            self.assertEqual(unsupported[0]["unparsed_nested_calls"], 1)
            self.assertIsNone(unsupported[0]["reported_success"])

    def test_context_extractor_preserves_surrounding_messages_and_origin_hints(self) -> None:
        """Extract cited context without treating a harness envelope as direct authority."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = root / "rollout.jsonl"
            records = [
                {"type": "session_meta", "payload": {"id": "rollout-context"}},
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": "Inspect this trace only."}],
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "I will inspect the selected event."}],
                    },
                },
                {
                    "type": "response_item",
                    "payload": {"type": "custom_tool_call", "id": "call-context", "name": "exec", "input": "tool input"},
                },
                {
                    "type": "response_item",
                    "payload": {"type": "custom_tool_call_output", "call_id": "call-context", "output": "tool output"},
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": '<codex_internal_context source="goal">Continue</codex_internal_context>',
                            }
                        ],
                    },
                },
            ]
            session.write_text("".join(json.dumps(item) + "\n" for item in records), encoding="utf-8")
            selection = root / "selection.json"
            write_json(
                selection,
                {
                    "schema_version": 1,
                    "defaults": {"before": 2, "after": 2, "max_excerpt_chars": 2_000},
                    "anchors": [{"id": "edit", "session_index": 0, "call_id": "call-context"}],
                },
            )
            output = root / "context.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "extract_rollout_context.py"),
                    "--session",
                    str(session),
                    "--selection",
                    str(selection),
                    "--output",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(output.read_text(encoding="utf-8"))
            events = result["anchors"][0]["events"]
            self.assertEqual(events[0]["origin_hint"], "direct_user_message")
            self.assertEqual(events[-1]["origin_hint"], "harness_internal_goal_context")
            self.assertEqual([event["kind"] for event in events], ["message", "message", "tool_call", "tool_output", "message"])


    def test_normalized_patch_targets_keep_repository_ownership(self) -> None:
        """Carry absolute and normalized targets through indexing and discovery."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            repository.mkdir()
            targets = {
                "relative": "src/relative.rs",
                "absolute": str(repository / "src/absolute.rs"),
                "normalized": "~/repository/src/normalized.rs",
                "outside-absolute": str(root / "outside.rs"),
                "outside-normalized": "~/outside.rs",
            }
            records = []
            for identifier, target in targets.items():
                patch = f"*** Begin Patch\n*** Add File: {target}\n+fixture\n*** End Patch\n"
                records.extend([
                    {"type": "response_item", "payload": {
                        "type": "custom_tool_call", "id": identifier, "name": "apply_patch", "input": patch,
                    }},
                    {"type": "response_item", "payload": {
                        "type": "custom_tool_call_output", "call_id": identifier, "output": {"exit_code": 0},
                    }},
                ])
            session = root / "session.jsonl"
            session.write_text("".join(json.dumps(item) + "\n" for item in records), encoding="utf-8")
            tool_index = root / "index.json"
            output = root / "candidates.json"
            args = ["discover_edit_candidates.py", "--tool-index", str(tool_index),
                    "--repository", str(repository), "--output", str(output)]
            with (
                mock.patch.object(Path, "home", return_value=root),
                mock.patch.object(damage_common, "HOME_PATH", str(root)),
                mock.patch.object(damage_common, "HOME_PATH_PATTERN", re.compile(
                    rf"{re.escape(str(root))}(?![A-Za-z0-9._-])"
                )),
                mock.patch.object(sys, "argv", args),
            ):
                write_json(tool_index, {"sessions": [index_rollout_tools.index_session(session, 0)]})
                self.assertEqual(discover_edit_candidates.main(), 0)
            result = json.loads(output.read_text(encoding="utf-8"))
            candidates = {item["call_id"]: item for item in result["candidates"]}
            self.assertEqual(set(candidates), {"relative", "absolute", "normalized"})
            for identifier in candidates:
                self.assertEqual(candidates[identifier]["operations"], [
                    {"operation": "add", "target": f"src/{identifier}.rs"}
                ])
            unsupported = result["unsupported_mutation_shaped_calls"]
            self.assertEqual({item["call_id"] for item in unsupported}, {
                "outside-absolute", "outside-normalized"
            })
            self.assertTrue(all(item["targets"] == ["~/outside.rs"] for item in unsupported))

    def test_reproducibility_requires_both_reports_from_successful_runs(self) -> None:
        """Missing reports and failed processes cannot pass the output gate."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            renderer = root / "fixture_renderer.py"
            renderer.write_text(
                'import argparse, json\n'
                'from pathlib import Path\n'
                'parser = argparse.ArgumentParser()\n'
                'for flag in ("manifest", "output-markdown", "output-json"):\n'
                '    parser.add_argument("--" + flag, required=True)\n'
                'args = parser.parse_args()\n'
                'config = json.loads(Path(args.manifest).read_text(encoding="utf-8"))\n'
                'skip = config.get("skip_run_b") and Path(args.output_json).parent.name == "run-b"\n'
                'if not skip:\n'
                '    for kind in config["outputs"]:\n'
                '        Path(getattr(args, "output_" + kind)).write_text(kind + "\\n", encoding="utf-8")\n'
                'raise SystemExit(config["exit_code"])\n',
                encoding="utf-8",
            )
            cases = [
                {"outputs": [], "exit_code": 0},
                {"outputs": ["markdown"], "exit_code": 0},
                {"outputs": ["json"], "exit_code": 0},
                {"outputs": ["markdown", "json"], "exit_code": 0, "skip_run_b": True},
                {"outputs": ["markdown", "json"], "exit_code": 7},
            ]
            for index, config in enumerate(cases):
                with self.subTest(config=config):
                    manifest_path = root / f"manifest-{index}.json"
                    write_json(manifest_path, config)
                    output = root / f"verification-{index}.json"
                    completed = subprocess.run([
                        sys.executable, str(SCRIPTS / "verify_damage_assessment.py"),
                        "--manifest", str(manifest_path), "--renderer", str(renderer),
                        "--output-root", str(root / f"runs-{index}"), "--output", str(output),
                    ], check=False, capture_output=True, text=True)
                    self.assertEqual(completed.returncode, 1, completed.stderr)
                    result = json.loads(output.read_text(encoding="utf-8"))
                    self.assertFalse(result["outputs_byte_identical"])
                    self.assertEqual([run["exit_code"] for run in result["runs"]], [config["exit_code"]] * 2)
                    for kind in ("markdown", "json"):
                        if config["exit_code"] or kind not in config["outputs"] or config.get("skip_run_b"):
                            self.assertFalse(result[f"{kind}_byte_identical"])

    def test_renderer_keeps_manifest_and_evidence_snapshots_attributable(self) -> None:
        """Hash consumed bytes even when both files change after their first read."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = fixture_evidence(root)
            evidence.write_bytes(evidence.read_bytes().replace(b"\n", b"\r\n"))
            evidence_hash = hash_file(evidence)
            value = manifest(evidence, evidence_hash)
            display_target = Path.home() / "audit-fixture"
            value["report"]["title"] = f"Evidence at {display_target}"
            exhibit = value["qualification_levels"][0]["representative_assessments"][0]["verbatim_exhibits"][0]
            exhibit["interpretation"]["text"] = f"Inspect {display_target}"
            manifest_path = root / "manifest.json"
            write_json(manifest_path, value)
            manifest_hash = hash_file(manifest_path)
            output = root / "report.json"
            markdown = root / "report.md"
            args = ["render_damage_assessment.py", "--manifest", str(manifest_path),
                    "--output-json", str(output), "--output-markdown", str(markdown)]
            replacement = b'{"replacement": true}\n'
            with replace_after_read({manifest_path: replacement, evidence: replacement}), mock.patch.object(sys, "argv", args):
                self.assertEqual(render_damage_assessment.main(), 0)
            result_text = output.read_text(encoding="utf-8")
            result = json.loads(result_text)
            self.assertEqual(result["manifest"]["sha256"], manifest_hash)
            self.assertEqual(result["evidence_inputs"][0]["sha256"], evidence_hash)
            self.assertEqual(result["qualification_levels"][0]["statistics"]["total"], 32)
            self.assertEqual(manifest_path.read_bytes(), replacement)
            self.assertEqual(evidence.read_bytes(), replacement)
            markdown_text = markdown.read_text(encoding="utf-8")
            self.assertIn("Evidence at ~/audit-fixture", markdown_text)
            self.assertIn("Inspect ~/audit-fixture", result_text)
            self.assertNotIn(str(Path.home()), markdown_text)
            self.assertNotIn(str(Path.home()), result_text)

    def test_evidence_loaders_keep_original_json_and_jsonl_hashes(self) -> None:
        """Preserve CRLF and blank-line bytes independently from parsed values."""
        cases = [
            ("json", b'{"fact": "before"}\r\n', {"fact": "before"}),
            ("jsonl", b'{"fact": "before"}\r\n\r\n{"fact": "second"}',
             [{"fact": "before"}, {"fact": "second"}]),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for format_name, data, expected in cases:
                with self.subTest(format=format_name):
                    path = root / f"facts.{format_name}"
                    path.write_bytes(data)
                    digest = hashlib.sha256(data).hexdigest()
                    declaration = {"evidence_inputs": [{
                        "id": "facts", "path": str(path), "sha256": digest,
                        "format": format_name, "role": "Snapshot fixture.",
                    }]}
                    with replace_after_read({path: b'{"fact": "after"}\n'}):
                        loaded, verified = render_damage_assessment.load_evidence(declaration, root / "manifest.json")
                    self.assertEqual(loaded["facts"], expected)
                    self.assertEqual(verified[0]["sha256"], digest)
                    self.assertNotEqual(hash_file(path), digest)

    def test_indexer_keeps_events_with_their_session_hash(self) -> None:
        """A later session replacement cannot relabel already captured events."""
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory) / "session.jsonl"
            record = {"type": "response_item", "payload": {
                "type": "custom_tool_call", "id": "before-call", "name": "exec",
                "input": "before input",
            }}
            data = (json.dumps(record) + "\r\n").encode("utf-8")
            session.write_bytes(data)
            with replace_after_read({session: b'{}\n'}):
                result = index_rollout_tools.index_session(session, 0)
            self.assertEqual(result["session_sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual(result["tool_events"][0]["input"], "before input")
            self.assertEqual(result["correlations"][0]["call_id"], "before-call")

    def test_context_extractor_keeps_selection_and_session_snapshots(self) -> None:
        """Context content and both recorded input hashes share their read snapshots."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = root / "session.jsonl"
            session.write_text(json.dumps({"type": "response_item", "payload": {
                "type": "custom_tool_call", "id": "before-call", "name": "exec", "input": "before input",
            }}) + "\n", encoding="utf-8")
            selection = root / "selection.json"
            write_json(selection, {
                "schema_version": 1,
                "defaults": {"before": 0, "after": 0, "max_excerpt_chars": 2_000},
                "anchors": [{"id": "before", "session_index": 0, "call_id": "before-call"}],
            })
            session_hash = hash_file(session)
            selection_hash = hash_file(selection)
            output = root / "context.json"
            args = ["extract_rollout_context.py", "--session", str(session),
                    "--selection", str(selection), "--output", str(output)]
            with replace_after_read({session: b'{}\n', selection: b'{}\n'}), mock.patch.object(sys, "argv", args):
                self.assertEqual(extract_rollout_context.main(), 0)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["selection"]["sha256"], selection_hash)
            self.assertEqual(result["sessions"][0]["session_sha256"], session_hash)
            self.assertEqual(result["anchors"][0]["call_id"], "before-call")
            self.assertEqual(result["anchors"][0]["events"][0]["text_excerpt"], "before input")

    def test_complete_exhibits_require_the_entire_selected_range(self) -> None:
        """Reject either omitted edge while allowing a complete explicit range."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = fixture_evidence(root)
            for index, (start, count, expected_exit) in enumerate([(1, 1, 1), (2, 1, 1), (1, 2, 0)]):
                with self.subTest(start=start, count=count):
                    value = manifest(evidence, hash_file(evidence))
                    exhibit = value["qualification_levels"][0]["representative_assessments"][2]["verbatim_exhibits"][0]
                    exhibit["source"]["start_line"] = start
                    exhibit["source"]["line_count"] = count
                    manifest_path = root / f"manifest-{index}.json"
                    write_json(manifest_path, value)
                    markdown = root / f"report-{index}.md"
                    output = root / f"report-{index}.json"
                    completed = subprocess.run([
                        sys.executable, str(SCRIPTS / "render_damage_assessment.py"), "--manifest", str(manifest_path),
                        "--output-markdown", str(markdown), "--output-json", str(output),
                    ], check=False, capture_output=True, text=True)
                    self.assertEqual(completed.returncode, expected_exit, completed.stderr)
                    if expected_exit:
                        self.assertIn("`complete_change` omits source lines", completed.stderr)
                        self.assertFalse(output.exists())
                        self.assertFalse(markdown.exists())
                    else:
                        result = json.loads(output.read_text(encoding="utf-8"))
                        dossiers = result["qualification_levels"][0]["representative_assessments"]
                        middle = next(item for item in dossiers if item["record_id"] == "middle")
                        self.assertEqual(middle["verbatim_exhibits"][0]["text"], "-old middle\n+new middle")

    def test_cli_input_errors_normalize_nested_home_paths(self) -> None:
        """Expose stable failures without leaking expanded paths or tracebacks."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = root / "missing-input"
            output = root / "unused-output.json"
            cases = [
                ("index_rollout_tools.py", ["--session", str(missing), "--output", str(output)]),
                ("discover_edit_candidates.py", ["--repository", str(root), "--tool-index", str(missing), "--output", str(output)]),
                ("discover_edit_candidates.py", ["--repository", str(missing), "--tool-index", str(output), "--output", str(output)]),
                ("extract_rollout_context.py", ["--session", str(missing), "--selection", str(missing), "--output", str(output)]),
                ("render_damage_assessment.py", ["--manifest", str(missing), "--output-json", str(output), "--output-markdown", str(root / "unused.md")]),
                ("verify_damage_assessment.py", ["--manifest", str(missing), "--output-root", str(root / "unused-runs"), "--output", str(output)]),
            ]
            for script, args in cases:
                with self.subTest(script=script, args=args):
                    completed = subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                                               check=False, capture_output=True, text=True)
                    self.assertEqual(completed.returncode, 1, completed.stderr)
                    self.assertEqual(completed.stdout, "")
                    self.assertIn(damage_common.display_path(missing), completed.stderr)
                    self.assertNotIn(str(Path.home()), completed.stderr)
                    self.assertNotIn("Traceback", completed.stderr)
                    self.assertFalse(output.exists())

    def test_snapshot_readers_reject_malformed_inputs(self) -> None:
        """Keep malformed JSON, JSONL records, and UTF-8 as located input failures."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-input"
            cases = [
                (damage_common.load_json_snapshot, b'{'),
                (damage_common.load_json_snapshot, b'\xff'),
                (damage_common.load_jsonl_snapshot, b'{}\n{'),
                (damage_common.load_jsonl_snapshot, b'[]\n'),
                (damage_common.load_jsonl_snapshot, b'\xff'),
            ]
            for loader, data in cases:
                with self.subTest(loader=loader.__name__, data=data):
                    path.write_bytes(data)
                    with self.assertRaises(damage_common.AssessmentInputError) as raised:
                        loader(path)
                    self.assertIn(damage_common.display_path(path), str(raised.exception))
                    self.assertNotIn(str(Path.home()), str(raised.exception))


if __name__ == "__main__":
    unittest.main()
