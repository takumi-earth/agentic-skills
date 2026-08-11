#!/usr/bin/env python3
"""Render a deterministic qualitative damage assessment from a cited manifest."""

from __future__ import annotations

import argparse
import re
import statistics
from pathlib import Path
from typing import Any

from damage_common import (
    AssessmentInputError,
    atomic_write_text,
    canonical_json,
    display_path,
    load_json,
    load_jsonl,
    require_exact_keys,
    require_list,
    require_object,
    require_string,
    require_string_list,
    require_unique,
    resolve_path,
    sha256_file,
)


TOP_LEVEL_REQUIRED = {"schema_version", "report", "evidence_inputs", "qualification_levels"}
REPORT_REQUIRED = {
    "title",
    "scope",
    "conclusion",
    "authority",
    "headline_facts",
    "terminology",
    "measurement_notes",
    "qualitative_changes",
    "decision_evidence_packets",
    "remediation_options",
    "recommendation",
    "limits",
}


def parse_args() -> argparse.Namespace:
    """Parse the manifest and deterministic output paths."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output-markdown", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    return parser.parse_args()


def table_text(value: str) -> str:
    """Escape one Markdown table cell without changing inline markup."""
    return value.replace("|", "\\|").replace("\n", "<br>")


def format_number(value: float) -> str:
    """Render a stable two-decimal statistic."""
    return f"{value:.2f}"


def validate_reference(reference: Any, evidence_ids: set[str], location: str) -> dict[str, str]:
    """Validate one typed evidence citation."""
    value = require_object(reference, location)
    require_exact_keys(value, {"input", "locator"}, set(), location)
    input_id = require_string(value["input"], f"{location}.input")
    locator = require_string(value["locator"], f"{location}.locator")
    if input_id not in evidence_ids:
        raise AssessmentInputError(f"{location}.input: unknown evidence input {input_id!r}")
    return {"input": input_id, "locator": locator}


def validate_references(value: Any, evidence_ids: set[str], location: str) -> list[dict[str, str]]:
    """Validate a nonempty citation list."""
    references = require_list(value, location)
    if not references:
        raise AssessmentInputError(f"{location}: expected at least one citation")
    return [validate_reference(reference, evidence_ids, f"{location}[{index}]") for index, reference in enumerate(references)]


def load_evidence(manifest: dict[str, Any], manifest_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load and hash every declared evidence input before assessment."""
    declarations = require_list(manifest["evidence_inputs"], "evidence_inputs")
    if not declarations:
        raise AssessmentInputError("evidence_inputs: expected at least one input")
    loaded: dict[str, Any] = {}
    verified: list[dict[str, Any]] = []
    identifiers: list[str] = []
    for index, declaration in enumerate(declarations):
        location = f"evidence_inputs[{index}]"
        value = require_object(declaration, location)
        require_exact_keys(value, {"id", "path", "sha256", "format", "role"}, set(), location)
        identifier = require_string(value["id"], f"{location}.id")
        path_text = require_string(value["path"], f"{location}.path")
        expected_hash = require_string(value["sha256"], f"{location}.sha256")
        format_name = require_string(value["format"], f"{location}.format")
        role = require_string(value["role"], f"{location}.role")
        if format_name not in {"json", "jsonl"}:
            raise AssessmentInputError(f"{location}.format: expected `json` or `jsonl`")
        path = resolve_path(path_text, manifest_path.parent).resolve(strict=True)
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            raise AssessmentInputError(
                f"{location}: SHA-256 mismatch for {display_path(path)}; expected {expected_hash}, got {actual_hash}"
            )
        identifiers.append(identifier)
        loaded[identifier] = load_json(path) if format_name == "json" else load_jsonl(path)
        verified.append(
            {
                "id": identifier,
                "path": display_path(path),
                "sha256": actual_hash,
                "format": format_name,
                "role": role,
            }
        )
    require_unique(identifiers, "evidence_inputs")
    return loaded, verified


def select_path(document: Any, steps: list[Any], location: str) -> Any:
    """Traverse object keys or array indices from one evidence document."""
    current = document
    for index, step in enumerate(steps):
        step_location = f"{location}.path[{index}]"
        if isinstance(step, str) and isinstance(current, dict) and step in current:
            current = current[step]
            continue
        if isinstance(step, int) and not isinstance(step, bool) and isinstance(current, list) and 0 <= step < len(current):
            current = current[step]
            continue
        raise AssessmentInputError(f"{step_location}: cannot traverse {step!r}")
    return current


def matches_predicate(observed: Any, predicate: Any, location: str) -> bool:
    """Match one exact value or one bounded declarative predicate."""
    if not isinstance(predicate, dict):
        return observed == predicate
    if not predicate:
        raise AssessmentInputError(f"{location}: expected at least one predicate operator")
    allowed = {"eq", "in", "gte", "lte"}
    unknown = set(predicate) - allowed
    if unknown:
        raise AssessmentInputError(f"{location}: unsupported predicate operator(s) {sorted(unknown)}")
    if "eq" in predicate and observed != predicate["eq"]:
        return False
    if "in" in predicate:
        choices = require_list(predicate["in"], f"{location}.in")
        if not choices:
            raise AssessmentInputError(f"{location}.in: expected at least one value")
        if isinstance(observed, list):
            if not any(item in choices for item in observed):
                return False
        elif observed not in choices:
            return False
    for operator in ("gte", "lte"):
        if operator not in predicate:
            continue
        boundary = predicate[operator]
        if (
            not isinstance(observed, (int, float))
            or isinstance(observed, bool)
            or not isinstance(boundary, (int, float))
            or isinstance(boundary, bool)
        ):
            raise AssessmentInputError(f"{location}.{operator}: expected numeric observed and boundary values")
        if operator == "gte" and observed < boundary:
            return False
        if operator == "lte" and observed > boundary:
            return False
    return True


def dotted_value(item: dict[str, Any], key: str) -> Any:
    """Resolve a dotted predicate key, flattening arrays of objects."""
    values: list[Any] = [item]
    for segment in key.split("."):
        next_values: list[Any] = []
        for value in values:
            if isinstance(value, dict) and segment in value:
                selected = value[segment]
                next_values.extend(selected if isinstance(selected, list) else [selected])
        values = next_values
        if not values:
            return None
    return values[0] if len(values) == 1 else values


def matches_where(item: Any, where: dict[str, Any], location: str) -> bool:
    """Return whether an object matches every shallow declarative predicate."""
    return isinstance(item, dict) and all(
        matches_predicate(dotted_value(item, key), expected, f"{location}.{key}")
        for key, expected in where.items()
    )


def select_evidence(evidence: dict[str, Any], selector: dict[str, Any], location: str) -> Any:
    """Resolve one manifest selector against a verified evidence input."""
    require_exact_keys(selector, {"input", "path"}, {"where"}, location)
    input_id = require_string(selector["input"], f"{location}.input")
    if input_id not in evidence:
        raise AssessmentInputError(f"{location}.input: unknown evidence input {input_id!r}")
    steps = require_list(selector["path"], f"{location}.path")
    for index, step in enumerate(steps):
        if not isinstance(step, (str, int)) or isinstance(step, bool):
            raise AssessmentInputError(f"{location}.path[{index}]: expected string key or integer index")
    selected = select_path(evidence[input_id], steps, location)
    if "where" not in selector:
        return selected
    where = require_object(selector["where"], f"{location}.where")
    if not where:
        raise AssessmentInputError(f"{location}.where: expected at least one predicate")
    if isinstance(selected, list):
        matches = [item for item in selected if matches_where(item, where, f"{location}.where")]
    else:
        matches = [selected] if matches_where(selected, where, f"{location}.where") else []
    if not matches:
        raise AssessmentInputError(f"{location}: selector matched no evidence records")
    return matches


def selected_records(value: Any) -> list[Any]:
    """Normalize one selected object or array into records."""
    return value if isinstance(value, list) else [value]


def numeric(value: Any, location: str) -> int:
    """Return a nonnegative integer metric component."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise AssessmentInputError(f"{location}: expected nonnegative integer")
    return value


def measure(measurement: Any, evidence: dict[str, Any], location: str) -> int:
    """Evaluate one generic evidence measurement expression."""
    value = require_object(measurement, location)
    require_exact_keys(value, {"select", "operation"}, {"fields", "field", "prefixes"}, location)
    selector = require_object(value["select"], f"{location}.select")
    selected = select_evidence(evidence, selector, f"{location}.select")
    records = selected_records(selected)
    operation = require_string(value["operation"], f"{location}.operation")
    if operation == "sum_fields":
        fields = require_string_list(value.get("fields"), f"{location}.fields")
        total = 0
        for record_index, record in enumerate(records):
            item = require_object(record, f"{location}.selection[{record_index}]")
            for field in fields:
                if field not in item:
                    raise AssessmentInputError(f"{location}.selection[{record_index}]: missing field {field!r}")
                total += numeric(item[field], f"{location}.selection[{record_index}].{field}")
        return total
    if operation == "field":
        field = require_string(value.get("field"), f"{location}.field")
        if len(records) != 1:
            raise AssessmentInputError(f"{location}: `field` requires exactly one selected record")
        item = require_object(records[0], f"{location}.selection[0]")
        if field not in item:
            raise AssessmentInputError(f"{location}.selection[0]: missing field {field!r}")
        return numeric(item[field], f"{location}.selection[0].{field}")
    if operation == "count_changed_lines":
        field = require_string(value.get("field"), f"{location}.field")
        prefixes = require_string_list(value.get("prefixes"), f"{location}.prefixes")
        total = 0
        for record_index, record in enumerate(records):
            item = require_object(record, f"{location}.selection[{record_index}]")
            lines = require_list(item.get(field), f"{location}.selection[{record_index}].{field}")
            for line_index, line in enumerate(lines):
                text = require_string(line, f"{location}.selection[{record_index}].{field}[{line_index}]")
                total += int(text.startswith(tuple(prefixes)))
        return total
    if operation == "count_records":
        return len(records)
    raise AssessmentInputError(f"{location}.operation: unsupported operation {operation!r}")


def compute_statistics(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate distribution statistics and deterministic real examples."""
    ordered = sorted(records, key=lambda record: (record["size"], record["identity"], record["id"]))
    values = [record["size"] for record in ordered]
    mean = statistics.fmean(values)
    median = float(statistics.median(values))
    minimum = values[0]
    maximum = values[-1]
    smallest_ties = [record for record in ordered if record["size"] == minimum]
    largest_ties = [record for record in ordered if record["size"] == maximum]
    distance = min(abs(record["size"] - mean) for record in ordered)
    mean_nearest = [record for record in ordered if abs(record["size"] - mean) == distance]
    midpoint = len(ordered) // 2
    median_examples = [ordered[midpoint]] if len(ordered) % 2 else [ordered[midpoint - 1], ordered[midpoint]]
    return {
        "count": len(ordered),
        "total": sum(values),
        "mean": round(mean, 2),
        "median": round(median, 2),
        "representatives": {
            "smallest": {"selected": smallest_ties[0], "tie_count": len(smallest_ties)},
            "largest": {"selected": largest_ties[0], "tie_count": len(largest_ties)},
            "mean_nearest": {"selected": mean_nearest, "distance": round(distance, 2)},
            "median": {"selected": median_examples},
        },
        "records": ordered,
    }


def validate_cited_statement(
    value: Any, evidence_ids: set[str], location: str
) -> dict[str, Any]:
    """Validate one decision-grade statement and its evidence citations."""
    statement = require_object(value, location)
    require_exact_keys(statement, {"text", "evidence_refs"}, set(), location)
    return {
        "text": require_string(statement["text"], f"{location}.text"),
        "evidence_refs": validate_references(
            statement["evidence_refs"], evidence_ids, f"{location}.evidence_refs"
        ),
    }


def validate_cited_statements(
    value: Any, evidence_ids: set[str], location: str
) -> list[dict[str, Any]]:
    """Validate a nonempty ordered list of cited statements."""
    statements = require_list(value, location)
    if not statements:
        raise AssessmentInputError(f"{location}: expected at least one statement")
    return [
        validate_cited_statement(statement, evidence_ids, f"{location}[{index}]")
        for index, statement in enumerate(statements)
    ]


def verbatim_text(value: Any, location: str) -> tuple[str, list[str]]:
    """Normalize one exact evidence string or ordered string array."""
    if isinstance(value, str):
        if not value:
            raise AssessmentInputError(f"{location}: expected nonempty verbatim text")
        return value, value.splitlines()
    lines = require_list(value, location)
    if not lines:
        raise AssessmentInputError(f"{location}: expected at least one verbatim line")
    exact_lines: list[str] = []
    for index, line in enumerate(lines):
        if not isinstance(line, str):
            raise AssessmentInputError(f"{location}[{index}]: expected a string")
        exact_lines.append(line)
    exact_text = "\n".join(exact_lines)
    if not exact_text:
        raise AssessmentInputError(f"{location}: resolved verbatim text is empty")
    return exact_text, exact_lines


def resolve_verbatim_source(value: Any, evidence: dict[str, Any], location: str) -> dict[str, Any]:
    """Resolve exact exhibit text from one hash-verified evidence selector."""
    source = require_object(value, location)
    require_exact_keys(source, {"select", "extract_path"}, {"start_line", "line_count"}, location)
    selector = require_object(source["select"], f"{location}.select")
    selected = select_evidence(evidence, selector, f"{location}.select")
    extract_path = require_list(source["extract_path"], f"{location}.extract_path")
    for index, step in enumerate(extract_path):
        if not isinstance(step, (str, int)) or isinstance(step, bool):
            raise AssessmentInputError(f"{location}.extract_path[{index}]: expected string key or integer index")
    extracted = select_path(selected, extract_path, f"{location}.extract_path")
    exact_text, lines = verbatim_text(extracted, f"{location}.resolved")
    has_start = "start_line" in source
    has_count = "line_count" in source
    if has_start != has_count:
        raise AssessmentInputError(f"{location}: `start_line` and `line_count` must be supplied together")
    if not has_start:
        return {"text": exact_text, "source": source}
    start_line = source["start_line"]
    line_count = source["line_count"]
    if not isinstance(start_line, int) or isinstance(start_line, bool) or start_line < 1:
        raise AssessmentInputError(f"{location}.start_line: expected a positive integer")
    if not isinstance(line_count, int) or isinstance(line_count, bool) or line_count < 1:
        raise AssessmentInputError(f"{location}.line_count: expected a positive integer")
    start_index = start_line - 1
    end_index = start_index + line_count
    if start_index >= len(lines) or end_index > len(lines):
        raise AssessmentInputError(
            f"{location}: line slice {start_line}..{end_index} exceeds {len(lines)} available line(s)"
        )
    return {"text": "\n".join(lines[start_index:end_index]), "source": source}


def resolve_evidence_collection_source(
    value: Any,
    evidence: dict[str, Any],
    location: str,
) -> list[dict[str, str]]:
    """Resolve an ordered collection of exact trace fragments."""
    source = require_object(value, location)
    require_exact_keys(source, {"select", "extract_each_path", "label_fields"}, set(), location)
    selector = require_object(source["select"], f"{location}.select")
    selected = select_evidence(evidence, selector, f"{location}.select")
    records = selected_records(selected)
    extract_path = require_list(source["extract_each_path"], f"{location}.extract_each_path")
    for index, step in enumerate(extract_path):
        if not isinstance(step, (str, int)) or isinstance(step, bool):
            raise AssessmentInputError(
                f"{location}.extract_each_path[{index}]: expected string key or integer index"
            )
    label_fields = require_string_list(source["label_fields"], f"{location}.label_fields")
    fragments: list[dict[str, str]] = []
    for index, record in enumerate(records):
        record_location = f"{location}.records[{index}]"
        record_object = require_object(record, record_location)
        extracted = select_path(record_object, extract_path, f"{record_location}.extract_each_path")
        exact_text, _lines = verbatim_text(extracted, f"{record_location}.resolved")
        labels: list[str] = []
        for field in label_fields:
            if field not in record_object:
                raise AssessmentInputError(f"{record_location}: missing label field {field!r}")
            label_value = record_object[field]
            if not isinstance(label_value, (str, int, float, bool)) or label_value == "":
                raise AssessmentInputError(f"{record_location}.{field}: expected a scalar label value")
            labels.append(f"{field}={label_value}")
        fragments.append({"label": "; ".join(labels), "text": exact_text})
    if not fragments:
        raise AssessmentInputError(f"{location}: expected at least one resolved fragment")
    return fragments


def validate_verbatim_exhibit(
    value: Any,
    evidence: dict[str, Any],
    evidence_ids: set[str],
    location: str,
) -> dict[str, Any]:
    """Validate and resolve one decision-grade verbatim exhibit."""
    exhibit = require_object(value, location)
    require_exact_keys(
        exhibit,
        {"title", "language", "scope", "effect_state", "source", "interpretation", "evidence_refs"},
        {"omitted"},
        location,
    )
    language = require_string(exhibit["language"], f"{location}.language")
    if re.fullmatch(r"[A-Za-z0-9_+.-]+", language) is None:
        raise AssessmentInputError(f"{location}.language: expected a Markdown fence language token")
    scope = require_string(exhibit["scope"], f"{location}.scope")
    if scope not in {"complete_change", "selected_excerpt"}:
        raise AssessmentInputError(f"{location}.scope: expected `complete_change` or `selected_excerpt`")
    effect_state = require_string(exhibit["effect_state"], f"{location}.effect_state")
    if effect_state not in {"landed", "attempted_not_landed", "prior_state"}:
        raise AssessmentInputError(
            f"{location}.effect_state: expected `landed`, `attempted_not_landed`, or `prior_state`"
        )
    omitted = exhibit.get("omitted")
    if scope == "selected_excerpt" and omitted is None:
        raise AssessmentInputError(f"{location}.omitted: required for a selected excerpt")
    if scope == "complete_change" and omitted is not None:
        raise AssessmentInputError(f"{location}.omitted: forbidden for a complete change")
    resolved = resolve_verbatim_source(exhibit["source"], evidence, f"{location}.source")
    return {
        "title": require_string(exhibit["title"], f"{location}.title"),
        "language": language,
        "scope": scope,
        "effect_state": effect_state,
        "source": resolved["source"],
        "text": resolved["text"],
        "interpretation": validate_cited_statement(
            exhibit["interpretation"], evidence_ids, f"{location}.interpretation"
        ),
        "evidence_refs": validate_references(exhibit["evidence_refs"], evidence_ids, f"{location}.evidence_refs"),
        "omitted": None if omitted is None else require_string(omitted, f"{location}.omitted"),
    }


def representative_role_map(statistics_value: dict[str, Any]) -> dict[str, list[str]]:
    """Map every unique computed representative to all statistical roles it fills."""
    representatives = statistics_value["representatives"]
    role_records = [
        ("smallest", [representatives["smallest"]["selected"]]),
        ("largest", [representatives["largest"]["selected"]]),
        ("mean-nearest", representatives["mean_nearest"]["selected"]),
        ("median", representatives["median"]["selected"]),
    ]
    roles: dict[str, list[str]] = {}
    for role, records in role_records:
        for record in records:
            record_roles = roles.setdefault(record["id"], [])
            if role not in record_roles:
                record_roles.append(role)
    return roles


def validate_dossier(
    value: Any,
    evidence: dict[str, Any],
    evidence_ids: set[str],
    records: dict[str, dict[str, Any]],
    role_map: dict[str, list[str]],
    location: str,
) -> dict[str, Any]:
    """Validate one complete qualitative decision dossier for a representative."""
    dossier = require_object(value, location)
    require_exact_keys(
        dossier,
        {
            "record_id",
            "title",
            "verbatim_exhibits",
            "summary",
            "prior_state",
            "change",
            "trace_context",
            "stated_rationale",
            "authority_assessment",
            "behavioral_effects",
            "causal_dependencies",
            "keep_consequences",
            "reverse_consequences",
            "recommended_disposition",
            "confidence",
            "unknowns",
        },
        set(),
        location,
    )
    record_id = require_string(dossier["record_id"], f"{location}.record_id")
    if record_id not in records:
        raise AssessmentInputError(f"{location}.record_id: unknown record {record_id!r}")
    if record_id not in role_map:
        raise AssessmentInputError(f"{location}.record_id: record is not a computed representative")
    authority = require_object(dossier["authority_assessment"], f"{location}.authority_assessment")
    require_exact_keys(authority, {"status", "assessment"}, set(), f"{location}.authority_assessment")
    authority_status = require_string(authority["status"], f"{location}.authority_assessment.status")
    allowed_authority = {"explicitly_authorized", "unauthorized", "mixed_authority", "indeterminate"}
    if authority_status not in allowed_authority:
        raise AssessmentInputError(
            f"{location}.authority_assessment.status: expected one of {sorted(allowed_authority)}"
        )
    disposition = require_object(
        dossier["recommended_disposition"], f"{location}.recommended_disposition"
    )
    require_exact_keys(
        disposition,
        {"action", "reasons", "risks"},
        set(),
        f"{location}.recommended_disposition",
    )
    confidence = require_object(dossier["confidence"], f"{location}.confidence")
    require_exact_keys(confidence, {"level", "basis"}, set(), f"{location}.confidence")
    confidence_level = require_string(confidence["level"], f"{location}.confidence.level")
    if confidence_level not in {"high", "medium", "low"}:
        raise AssessmentInputError(f"{location}.confidence.level: expected `high`, `medium`, or `low`")
    exhibit_values = require_list(dossier["verbatim_exhibits"], f"{location}.verbatim_exhibits")
    if not exhibit_values:
        raise AssessmentInputError(f"{location}.verbatim_exhibits: expected at least one exact exhibit")
    return {
        "record_id": record_id,
        "record": records[record_id],
        "representative_roles": role_map[record_id],
        "title": require_string(dossier["title"], f"{location}.title"),
        "verbatim_exhibits": [
            validate_verbatim_exhibit(
                exhibit,
                evidence,
                evidence_ids,
                f"{location}.verbatim_exhibits[{index}]",
            )
            for index, exhibit in enumerate(exhibit_values)
        ],
        "summary": validate_cited_statement(dossier["summary"], evidence_ids, f"{location}.summary"),
        "prior_state": validate_cited_statement(
            dossier["prior_state"], evidence_ids, f"{location}.prior_state"
        ),
        "change": validate_cited_statement(dossier["change"], evidence_ids, f"{location}.change"),
        "trace_context": validate_cited_statements(
            dossier["trace_context"], evidence_ids, f"{location}.trace_context"
        ),
        "stated_rationale": validate_cited_statement(
            dossier["stated_rationale"], evidence_ids, f"{location}.stated_rationale"
        ),
        "authority_assessment": {
            "status": authority_status,
            "assessment": validate_cited_statement(
                authority["assessment"], evidence_ids, f"{location}.authority_assessment.assessment"
            ),
        },
        "behavioral_effects": validate_cited_statements(
            dossier["behavioral_effects"], evidence_ids, f"{location}.behavioral_effects"
        ),
        "causal_dependencies": validate_cited_statements(
            dossier["causal_dependencies"], evidence_ids, f"{location}.causal_dependencies"
        ),
        "keep_consequences": validate_cited_statements(
            dossier["keep_consequences"], evidence_ids, f"{location}.keep_consequences"
        ),
        "reverse_consequences": validate_cited_statements(
            dossier["reverse_consequences"], evidence_ids, f"{location}.reverse_consequences"
        ),
        "recommended_disposition": {
            "action": validate_cited_statement(
                disposition["action"], evidence_ids, f"{location}.recommended_disposition.action"
            ),
            "reasons": validate_cited_statements(
                disposition["reasons"], evidence_ids, f"{location}.recommended_disposition.reasons"
            ),
            "risks": validate_cited_statements(
                disposition["risks"], evidence_ids, f"{location}.recommended_disposition.risks"
            ),
        },
        "confidence": {
            "level": confidence_level,
            "basis": validate_cited_statement(
                confidence["basis"], evidence_ids, f"{location}.confidence.basis"
            ),
        },
        "unknowns": require_string_list(
            dossier["unknowns"], f"{location}.unknowns", allow_empty=True
        ),
    }


def validate_record(value: Any, evidence: dict[str, Any], evidence_ids: set[str], location: str) -> dict[str, Any]:
    """Validate and measure one qualification record."""
    record = require_object(value, location)
    require_exact_keys(
        record,
        {"id", "identity", "description", "landed_state", "candidate_state", "evidence_refs", "measurement"},
        set(),
        location,
    )
    result = {
        "id": require_string(record["id"], f"{location}.id"),
        "identity": require_string(record["identity"], f"{location}.identity"),
        "description": require_string(record["description"], f"{location}.description"),
        "landed_state": require_string(record["landed_state"], f"{location}.landed_state"),
        "candidate_state": require_string(record["candidate_state"], f"{location}.candidate_state"),
        "evidence_refs": validate_references(record["evidence_refs"], evidence_ids, f"{location}.evidence_refs"),
        "measurement": record["measurement"],
    }
    result["size"] = measure(record["measurement"], evidence, f"{location}.measurement")
    return result


def validate_levels(value: Any, evidence: dict[str, Any], evidence_ids: set[str]) -> list[dict[str, Any]]:
    """Validate every qualification level and compute its statistics."""
    levels = require_list(value, "qualification_levels")
    if not levels:
        raise AssessmentInputError("qualification_levels: expected at least one level")
    results: list[dict[str, Any]] = []
    level_ids: list[str] = []
    for level_index, level_value in enumerate(levels):
        location = f"qualification_levels[{level_index}]"
        level = require_object(level_value, location)
        require_exact_keys(
            level,
            {
                "id",
                "title",
                "definition",
                "metric",
                "automatic_action",
                "records",
                "representative_assessments",
            },
            set(),
            location,
        )
        metric = require_object(level["metric"], f"{location}.metric")
        require_exact_keys(metric, {"name", "unit", "caveat"}, set(), f"{location}.metric")
        records_source = require_list(level["records"], f"{location}.records")
        if not records_source:
            raise AssessmentInputError(f"{location}.records: expected at least one record")
        records = [
            validate_record(record, evidence, evidence_ids, f"{location}.records[{record_index}]")
            for record_index, record in enumerate(records_source)
        ]
        require_unique([record["id"] for record in records], f"{location}.records")
        identifier = require_string(level["id"], f"{location}.id")
        level_ids.append(identifier)
        statistics_value = compute_statistics(records)
        roles = representative_role_map(statistics_value)
        record_by_id = {record["id"]: record for record in records}
        assessment_values = require_list(
            level["representative_assessments"], f"{location}.representative_assessments"
        )
        assessments = [
            validate_dossier(
                assessment,
                evidence,
                evidence_ids,
                record_by_id,
                roles,
                f"{location}.representative_assessments[{assessment_index}]",
            )
            for assessment_index, assessment in enumerate(assessment_values)
        ]
        assessment_ids = [assessment["record_id"] for assessment in assessments]
        require_unique(assessment_ids, f"{location}.representative_assessments")
        missing = sorted(set(roles) - set(assessment_ids))
        extra = sorted(set(assessment_ids) - set(roles))
        if missing or extra:
            raise AssessmentInputError(
                f"{location}.representative_assessments: dossier mismatch; missing {missing}, extra {extra}"
            )
        assessment_by_id = {assessment["record_id"]: assessment for assessment in assessments}
        ordered_assessments = [assessment_by_id[record_id] for record_id in roles]
        results.append(
            {
                "id": identifier,
                "title": require_string(level["title"], f"{location}.title"),
                "definition": require_string(level["definition"], f"{location}.definition"),
                "metric": {
                    "name": require_string(metric["name"], f"{location}.metric.name"),
                    "unit": require_string(metric["unit"], f"{location}.metric.unit"),
                    "caveat": require_string(metric["caveat"], f"{location}.metric.caveat"),
                },
                "automatic_action": require_string(level["automatic_action"], f"{location}.automatic_action"),
                "statistics": statistics_value,
                "representative_assessments": ordered_assessments,
            }
        )
    require_unique(level_ids, "qualification_levels")
    return results


def validate_evidence_collection(
    value: Any,
    evidence: dict[str, Any],
    evidence_ids: set[str],
    location: str,
) -> dict[str, Any]:
    """Validate one complete, expandable collection of exact trace fragments."""
    collection = require_object(value, location)
    require_exact_keys(
        collection,
        {"title", "language", "effect_state", "description", "source", "evidence_refs"},
        set(),
        location,
    )
    effect_state = require_string(collection["effect_state"], f"{location}.effect_state")
    if effect_state not in {"landed", "attempted_not_landed", "unresolved"}:
        raise AssessmentInputError(
            f"{location}.effect_state: expected `landed`, `attempted_not_landed`, or `unresolved`"
        )
    language = require_string(collection["language"], f"{location}.language")
    if re.fullmatch(r"[A-Za-z0-9_+.-]+", language) is None:
        raise AssessmentInputError(f"{location}.language: expected a Markdown fence language token")
    return {
        "title": require_string(collection["title"], f"{location}.title"),
        "language": language,
        "effect_state": effect_state,
        "description": require_string(collection["description"], f"{location}.description"),
        "fragments": resolve_evidence_collection_source(collection["source"], evidence, f"{location}.source"),
        "evidence_refs": validate_references(
            collection["evidence_refs"], evidence_ids, f"{location}.evidence_refs"
        ),
    }


def validate_decision_evidence_packet(
    value: Any,
    evidence: dict[str, Any],
    evidence_ids: set[str],
    location: str,
) -> dict[str, Any]:
    """Validate one self-contained evidence packet used by remediation verdicts."""
    packet = require_object(value, location)
    require_exact_keys(
        packet,
        {"id", "title", "summary", "changes", "trace_appendix", "evidence_refs"},
        set(),
        location,
    )
    change_values = require_list(packet["changes"], f"{location}.changes")
    if not change_values:
        raise AssessmentInputError(f"{location}.changes: expected at least one semantic change")
    changes: list[dict[str, Any]] = []
    change_ids: list[str] = []
    for index, change_value in enumerate(change_values):
        change_location = f"{location}.changes[{index}]"
        change = require_object(change_value, change_location)
        require_exact_keys(
            change,
            {"id", "title", "artifacts", "what_changed", "why_it_matters", "evidence_refs"},
            set(),
            change_location,
        )
        identifier = require_string(change["id"], f"{change_location}.id")
        change_ids.append(identifier)
        changes.append(
            {
                "id": identifier,
                "title": require_string(change["title"], f"{change_location}.title"),
                "artifacts": require_string_list(change["artifacts"], f"{change_location}.artifacts"),
                "what_changed": require_string_list(change["what_changed"], f"{change_location}.what_changed"),
                "why_it_matters": require_string_list(
                    change["why_it_matters"], f"{change_location}.why_it_matters"
                ),
                "evidence_refs": validate_references(
                    change["evidence_refs"], evidence_ids, f"{change_location}.evidence_refs"
                ),
            }
        )
    require_unique(change_ids, f"{location}.changes")
    identifier = require_string(packet["id"], f"{location}.id")
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier) is None:
        raise AssessmentInputError(f"{location}.id: expected a lowercase hyphenated anchor identifier")
    return {
        "id": identifier,
        "title": require_string(packet["title"], f"{location}.title"),
        "summary": require_string(packet["summary"], f"{location}.summary"),
        "changes": changes,
        "trace_appendix": validate_evidence_collection(
            packet["trace_appendix"], evidence, evidence_ids, f"{location}.trace_appendix"
        ),
        "evidence_refs": validate_references(packet["evidence_refs"], evidence_ids, f"{location}.evidence_refs"),
    }


def validate_remediation_unit(value: Any, evidence_ids: set[str], location: str) -> dict[str, Any]:
    """Validate one concrete retain/remove/decision mapping."""
    unit = require_object(value, location)
    require_exact_keys(
        unit,
        {
            "id",
            "title",
            "artifacts",
            "evidence_packet",
            "retain",
            "remove_or_restore",
            "requires_decision",
            "approved_means",
            "rejected_means",
            "reason",
            "evidence_refs",
        },
        set(),
        location,
    )
    retain = require_string_list(unit["retain"], f"{location}.retain", allow_empty=True)
    remove_or_restore = require_string_list(
        unit["remove_or_restore"], f"{location}.remove_or_restore", allow_empty=True
    )
    requires_decision = require_string_list(
        unit["requires_decision"], f"{location}.requires_decision", allow_empty=True
    )
    if not retain and not remove_or_restore and not requires_decision:
        raise AssessmentInputError(
            f"{location}: expected at least one retained, removed/restored, or undecided outcome"
        )
    return {
        "id": require_string(unit["id"], f"{location}.id"),
        "title": require_string(unit["title"], f"{location}.title"),
        "artifacts": require_string_list(unit["artifacts"], f"{location}.artifacts"),
        "evidence_packet": require_string(unit["evidence_packet"], f"{location}.evidence_packet"),
        "retain": retain,
        "remove_or_restore": remove_or_restore,
        "requires_decision": requires_decision,
        "approved_means": require_string_list(unit["approved_means"], f"{location}.approved_means"),
        "rejected_means": require_string_list(unit["rejected_means"], f"{location}.rejected_means"),
        "reason": require_string(unit["reason"], f"{location}.reason"),
        "evidence_refs": validate_references(unit["evidence_refs"], evidence_ids, f"{location}.evidence_refs"),
    }


def validate_report(value: Any, evidence: dict[str, Any], evidence_ids: set[str]) -> dict[str, Any]:
    """Validate incident prose and cited qualitative judgments."""
    report = require_object(value, "report")
    require_exact_keys(report, REPORT_REQUIRED, set(), "report")
    fact_values = require_list(report["headline_facts"], "report.headline_facts")
    if not fact_values:
        raise AssessmentInputError("report.headline_facts: expected at least one fact")
    facts: list[dict[str, Any]] = []
    fact_ids: list[str] = []
    for fact_index, fact_value in enumerate(fact_values):
        location = f"report.headline_facts[{fact_index}]"
        fact = require_object(fact_value, location)
        require_exact_keys(fact, {"id", "label", "unit", "description", "evidence_refs", "measurement"}, set(), location)
        identifier = require_string(fact["id"], f"{location}.id")
        fact_ids.append(identifier)
        facts.append(
            {
                "id": identifier,
                "label": require_string(fact["label"], f"{location}.label"),
                "unit": require_string(fact["unit"], f"{location}.unit"),
                "description": require_string(fact["description"], f"{location}.description"),
                "evidence_refs": validate_references(fact["evidence_refs"], evidence_ids, f"{location}.evidence_refs"),
                "measurement": fact["measurement"],
                "value": measure(fact["measurement"], evidence, f"{location}.measurement"),
            }
        )
    require_unique(fact_ids, "report.headline_facts")
    terminology_values = require_list(report["terminology"], "report.terminology")
    terminology: list[dict[str, Any]] = []
    for index, item_value in enumerate(terminology_values):
        location = f"report.terminology[{index}]"
        item = require_object(item_value, location)
        require_exact_keys(item, {"term", "definition", "not_equivalent_to", "examples"}, set(), location)
        terminology.append(
            {
                "term": require_string(item["term"], f"{location}.term"),
                "definition": require_string(item["definition"], f"{location}.definition"),
                "not_equivalent_to": require_string_list(item["not_equivalent_to"], f"{location}.not_equivalent_to"),
                "examples": require_string_list(item["examples"], f"{location}.examples"),
            }
        )
    changes_values = require_list(report["qualitative_changes"], "report.qualitative_changes")
    if not changes_values:
        raise AssessmentInputError("report.qualitative_changes: expected at least one change group")
    changes: list[dict[str, Any]] = []
    change_ids: list[str] = []
    for change_index, change_value in enumerate(changes_values):
        location = f"report.qualitative_changes[{change_index}]"
        change = require_object(change_value, location)
        require_exact_keys(change, {"id", "title", "summary", "impacts", "examples"}, set(), location)
        examples_values = require_list(change["examples"], f"{location}.examples")
        if not examples_values:
            raise AssessmentInputError(f"{location}.examples: expected at least one example")
        examples: list[dict[str, Any]] = []
        for example_index, example_value in enumerate(examples_values):
            example_location = f"{location}.examples[{example_index}]"
            example = require_object(example_value, example_location)
            require_exact_keys(example, {"identity", "description", "evidence_refs"}, set(), example_location)
            examples.append(
                {
                    "identity": require_string(example["identity"], f"{example_location}.identity"),
                    "description": require_string(example["description"], f"{example_location}.description"),
                    "evidence_refs": validate_references(
                        example["evidence_refs"], evidence_ids, f"{example_location}.evidence_refs"
                    ),
                }
            )
        identifier = require_string(change["id"], f"{location}.id")
        change_ids.append(identifier)
        changes.append(
            {
                "id": identifier,
                "title": require_string(change["title"], f"{location}.title"),
                "summary": require_string(change["summary"], f"{location}.summary"),
                "impacts": require_string_list(change["impacts"], f"{location}.impacts"),
                "examples": examples,
            }
        )
    require_unique(change_ids, "report.qualitative_changes")
    packet_values = require_list(report["decision_evidence_packets"], "report.decision_evidence_packets")
    if not packet_values:
        raise AssessmentInputError("report.decision_evidence_packets: expected at least one packet")
    decision_evidence_packets = [
        validate_decision_evidence_packet(
            packet,
            evidence,
            evidence_ids,
            f"report.decision_evidence_packets[{index}]",
        )
        for index, packet in enumerate(packet_values)
    ]
    packet_ids = [packet["id"] for packet in decision_evidence_packets]
    require_unique(packet_ids, "report.decision_evidence_packets")
    packet_id_set = set(packet_ids)
    option_values = require_list(report["remediation_options"], "report.remediation_options")
    options: list[dict[str, Any]] = []
    roles: list[str] = []
    for option_index, option_value in enumerate(option_values):
        location = f"report.remediation_options[{option_index}]"
        option = require_object(option_value, location)
        require_exact_keys(
            option,
            {"role", "title", "summary", "actions", "decision_units", "reasons", "risks"},
            set(),
            location,
        )
        role = require_string(option["role"], f"{location}.role")
        roles.append(role)
        unit_values = require_list(option["decision_units"], f"{location}.decision_units")
        if not unit_values:
            raise AssessmentInputError(f"{location}.decision_units: expected at least one concrete unit")
        decision_units = [
            validate_remediation_unit(unit, evidence_ids, f"{location}.decision_units[{index}]")
            for index, unit in enumerate(unit_values)
        ]
        require_unique([unit["id"] for unit in decision_units], f"{location}.decision_units")
        for index, unit in enumerate(decision_units):
            if unit["evidence_packet"] not in packet_id_set:
                raise AssessmentInputError(
                    f"{location}.decision_units[{index}].evidence_packet: unknown packet {unit['evidence_packet']!r}"
                )
        options.append(
            {
                "role": role,
                "title": require_string(option["title"], f"{location}.title"),
                "summary": require_string(option["summary"], f"{location}.summary"),
                "actions": require_string_list(option["actions"], f"{location}.actions"),
                "decision_units": decision_units,
                "reasons": require_string_list(option["reasons"], f"{location}.reasons"),
                "risks": require_string_list(option["risks"], f"{location}.risks"),
            }
        )
    require_unique(roles, "report.remediation_options")
    required_roles = {"aggressive", "conservative", "recommended"}
    if set(roles) != required_roles:
        raise AssessmentInputError(f"report.remediation_options: expected roles {sorted(required_roles)}, got {sorted(roles)}")
    referenced_packets = {
        unit["evidence_packet"] for option in options for unit in option["decision_units"]
    }
    unreferenced_packets = sorted(packet_id_set - referenced_packets)
    if unreferenced_packets:
        raise AssessmentInputError(
            f"report.decision_evidence_packets: unreferenced packet(s) {unreferenced_packets}"
        )
    recommendation = require_string(report["recommendation"], "report.recommendation")
    if recommendation not in roles:
        raise AssessmentInputError("report.recommendation: must name a remediation role")
    return {
        "title": require_string(report["title"], "report.title"),
        "scope": require_string_list(report["scope"], "report.scope"),
        "conclusion": require_string_list(report["conclusion"], "report.conclusion"),
        "authority": require_string_list(report["authority"], "report.authority"),
        "headline_facts": facts,
        "terminology": terminology,
        "measurement_notes": require_string_list(report["measurement_notes"], "report.measurement_notes"),
        "qualitative_changes": changes,
        "decision_evidence_packets": decision_evidence_packets,
        "remediation_options": options,
        "recommendation": recommendation,
        "limits": require_string_list(report["limits"], "report.limits"),
    }


def citation_text(references: list[dict[str, str]]) -> str:
    """Render typed evidence references compactly."""
    return "; ".join(f"`{reference['input']}` → `{reference['locator']}`" for reference in references)


def append_cited_statement(
    lines: list[str], label: str, statement: dict[str, Any]
) -> None:
    """Append one self-contained statement followed by its typed evidence."""
    lines.append(f"**{label}.** {statement['text']}")
    lines.append("")
    lines.append(f"Evidence: {citation_text(statement['evidence_refs'])}.")


def append_cited_list(
    lines: list[str], label: str, statements: list[dict[str, Any]]
) -> None:
    """Append one labeled list whose every judgment carries citations."""
    lines.extend([f"**{label}.**", ""])
    for statement in statements:
        lines.append(f"- {statement['text']}")
        lines.append(f"  - Evidence: {citation_text(statement['evidence_refs'])}.")


def representative_rows(level: dict[str, Any]) -> list[tuple[str, list[dict[str, Any]], str]]:
    """Return the four computed representative roles for a compact map."""
    representatives = level["statistics"]["representatives"]
    return [
        (
            "smallest",
            [representatives["smallest"]["selected"]],
            f"minimum; `{representatives['smallest']['tie_count']}` record(s) share it",
        ),
        (
            "largest",
            [representatives["largest"]["selected"]],
            f"maximum; `{representatives['largest']['tie_count']}` record(s) share it",
        ),
        (
            "mean-nearest",
            representatives["mean_nearest"]["selected"],
            f"nearest real record(s), distance `{format_number(float(representatives['mean_nearest']['distance']))}`",
        ),
        ("median", representatives["median"]["selected"], "middle record or bracketing pair"),
    ]


def fenced_text(text: str, language: str) -> list[str]:
    """Wrap exact text in a fence longer than any backtick run it contains."""
    longest = max((len(match.group(0)) for match in re.finditer(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return [f"{fence}{language}", text, fence]


def append_verbatim_exhibit(lines: list[str], exhibit: dict[str, Any]) -> None:
    """Append exact evidence before its separate interpretation."""
    lines.extend(
        [
            f"**Verbatim change exhibit — {exhibit['title']}.**",
            "",
            f"- Effect state: `{exhibit['effect_state']}`.",
            f"- Exhibit coverage: `{exhibit['scope']}`.",
            "",
        ]
    )
    lines.extend(fenced_text(exhibit["text"], exhibit["language"]))
    lines.append("")
    append_cited_statement(lines, "What this exact text shows", exhibit["interpretation"])
    lines.append("")
    lines.append(f"Exhibit evidence: {citation_text(exhibit['evidence_refs'])}.")
    if exhibit["omitted"] is not None:
        lines.extend(["", f"**Omitted from this selected excerpt.** {exhibit['omitted']}"])


def append_dossier(lines: list[str], dossier: dict[str, Any], unit: str) -> None:
    """Append one de-duplicated qualitative decision dossier."""
    record = dossier["record"]
    roles = ", ".join(f"`{role}`" for role in dossier["representative_roles"])
    lines.extend(
        [
            f"##### `{record['id']}` — {dossier['title']}",
            "",
            f"- Statistical roles: {roles}.",
            f"- Artifact or operation: `{record['identity']}`.",
            f"- Measured size: `{record['size']}` {unit}. This selects the example; it does not rank severity.",
            f"- Landed state: `{record['landed_state']}`.",
            f"- Remediation-candidate state: `{record['candidate_state']}`.",
            "",
        ]
    )
    for exhibit in dossier["verbatim_exhibits"]:
        append_verbatim_exhibit(lines, exhibit)
        lines.append("")
    append_cited_statement(lines, "Decision summary", dossier["summary"])
    lines.append("")
    append_cited_statement(lines, "Before", dossier["prior_state"])
    lines.append("")
    append_cited_statement(lines, "What changed", dossier["change"])
    lines.append("")
    append_cited_list(lines, "Trace context", dossier["trace_context"])
    lines.append("")
    append_cited_statement(lines, "Stated rationale", dossier["stated_rationale"])
    lines.append("")
    lines.append(
        f"**Authority assessment — `{dossier['authority_assessment']['status']}`.** "
        f"{dossier['authority_assessment']['assessment']['text']}"
    )
    lines.append("")
    lines.append(
        f"Evidence: {citation_text(dossier['authority_assessment']['assessment']['evidence_refs'])}."
    )
    lines.append("")
    append_cited_list(lines, "Behavioral and architectural effects", dossier["behavioral_effects"])
    lines.append("")
    append_cited_list(lines, "Causal dependencies", dossier["causal_dependencies"])
    lines.append("")
    append_cited_list(lines, "If retained", dossier["keep_consequences"])
    lines.append("")
    append_cited_list(lines, "If reversed", dossier["reverse_consequences"])
    lines.append("")
    append_cited_statement(
        lines, "Recommended disposition", dossier["recommended_disposition"]["action"]
    )
    lines.append("")
    append_cited_list(lines, "Why", dossier["recommended_disposition"]["reasons"])
    lines.append("")
    append_cited_list(lines, "Risks of that disposition", dossier["recommended_disposition"]["risks"])
    lines.append("")
    lines.append(f"**Confidence — `{dossier['confidence']['level']}`.** {dossier['confidence']['basis']['text']}")
    lines.append("")
    lines.append(f"Evidence: {citation_text(dossier['confidence']['basis']['evidence_refs'])}.")
    lines.append("")
    lines.append("**Unknowns.**")
    lines.append("")
    if dossier["unknowns"]:
        lines.extend(f"- {unknown}" for unknown in dossier["unknowns"])
    else:
        lines.append("- None material to this disposition are currently identified.")


def append_decision_evidence_packet(lines: list[str], packet: dict[str, Any]) -> None:
    """Append one semantic decision inventory plus its complete trace appendix."""
    lines.extend(
        [
            f"<a id=\"decision-evidence-{packet['id']}\"></a>",
            "",
            f"### `{packet['id']}` — {packet['title']}",
            "",
            packet["summary"],
            "",
        ]
    )
    for change in packet["changes"]:
        lines.extend([f"#### `{change['id']}` — {change['title']}", "", "Artifacts or statements:", ""])
        lines.extend(f"- `{artifact}`" for artifact in change["artifacts"])
        lines.extend(["", "What changed:", ""])
        lines.extend(f"- {item}" for item in change["what_changed"])
        lines.extend(["", "Why it matters to the decision:", ""])
        lines.extend(f"- {item}" for item in change["why_it_matters"])
        lines.extend(["", f"Evidence: {citation_text(change['evidence_refs'])}.", ""])
    appendix = packet["trace_appendix"]
    lines.extend(
        [
            "<details>",
            f"<summary>{appendix['title']} — {len(appendix['fragments'])} exact fragment(s)</summary>",
            "",
            f"Effect state: `{appendix['effect_state']}`.",
            "",
            appendix["description"],
            "",
        ]
    )
    for index, fragment in enumerate(appendix["fragments"], start=1):
        lines.extend([f"##### Exact fragment `{index}` — `{fragment['label']}`", ""])
        lines.extend(fenced_text(fragment["text"], appendix["language"]))
        lines.append("")
    lines.extend(
        [
            f"Trace-appendix evidence: {citation_text(appendix['evidence_refs'])}.",
            "",
            "</details>",
            "",
            f"Packet evidence: {citation_text(packet['evidence_refs'])}.",
            "",
        ]
    )


def render_markdown(report: dict[str, Any], levels: list[dict[str, Any]], verified: list[dict[str, Any]], manifest_path: Path, manifest_hash: str) -> str:
    """Render the complete generic report from validated data."""
    lines = [f"# {report['title']}", "", "## Scope and conclusion", ""]
    lines.extend(f"- {item}" for item in report["scope"])
    lines.append("")
    lines.extend(f"- {item}" for item in report["conclusion"])
    lines.extend(["", "## Headline facts", "", "| Fact | Value | Meaning | Evidence |", "|---|---:|---|---|"])
    for fact in report["headline_facts"]:
        lines.append(
            f"| {table_text(fact['label'])} | `{fact['value']}` {table_text(fact['unit'])} | "
            f"{table_text(fact['description'])} | {table_text(citation_text(fact['evidence_refs']))} |"
        )
    lines.extend(["", "## Authority boundary", ""])
    lines.extend(f"- {item}" for item in report["authority"])
    lines.extend(["", "## Terminology", ""])
    for item in report["terminology"]:
        lines.extend([f"### {item['term']}", "", item["definition"], "", "This is not equivalent to:", ""])
        lines.extend(f"- {value}" for value in item["not_equivalent_to"])
        lines.extend(["", "Examples:", ""])
        lines.extend(f"- {value}" for value in item["examples"])
        lines.append("")
    lines.extend(["## Qualification model", "", "| Level | Meaning | Metric | Records | Automatic action |", "|---|---|---|---:|---|"])
    for level in levels:
        stats = level["statistics"]
        lines.append(
            f"| `{table_text(level['id'])}` {table_text(level['title'])} | {table_text(level['definition'])} | "
            f"{table_text(level['metric']['name'])} | `{stats['count']}` | {table_text(level['automatic_action'])} |"
        )
    lines.extend(["", "## Measurement method", ""])
    lines.extend(f"- {item}" for item in report["measurement_notes"])
    lines.extend(["", "## Qualification statistics and qualitative decision dossiers", ""])
    for level in levels:
        stats = level["statistics"]
        unit = level["metric"]["unit"]
        reps = stats["representatives"]
        lines.extend(
            [
                f"### `{level['id']}` — {level['title']}",
                "",
                level["definition"],
                "",
                f"Metric: {level['metric']['name']} in `{unit}`. {level['metric']['caveat']}",
                "",
                f"- Count: `{stats['count']}`",
                f"- Total: `{stats['total']}` {unit}",
                f"- Mean: `{format_number(float(stats['mean']))}` {unit}",
                f"- Median: `{format_number(float(stats['median']))}` {unit}",
                "",
                "#### Representative map",
                "",
                "| Statistical role | Selected record(s) | Size(s) | Selection rule |",
                "|---|---|---:|---|",
            ]
        )
        for role, records, rule in representative_rows(level):
            identities = ", ".join(f"`{record['id']}` (`{record['identity']}`)" for record in records)
            sizes = ", ".join(f"`{record['size']}`" for record in records)
            lines.append(f"| `{role}` | {identities} | {sizes} {unit} | {rule} |")
        lines.extend(["", "A record that fills more than one role appears once below with all roles attached.", ""])
        lines.extend(["#### Qualitative decision dossiers", ""])
        for dossier in level["representative_assessments"]:
            append_dossier(lines, dossier, unit)
            lines.append("")
        lines.extend(
            [
                "",
                "#### Complete inventory",
                "",
                "| Record | Identity | Size | Landed state | Candidate state | Description | Evidence |",
                "|---|---|---:|---|---|---|---|",
            ]
        )
        for record in stats["records"]:
            lines.append(
                f"| `{table_text(record['id'])}` | `{table_text(record['identity'])}` | `{record['size']}` | "
                f"`{table_text(record['landed_state'])}` | `{table_text(record['candidate_state'])}` | "
                f"{table_text(record['description'])} | {table_text(citation_text(record['evidence_refs']))} |"
            )
        lines.append("")
    lines.extend(["## Qualitative changes", ""])
    for change in report["qualitative_changes"]:
        lines.extend([f"### {change['title']}", "", change["summary"], "", "Impacts:", ""])
        lines.extend(f"- {impact}" for impact in change["impacts"])
        lines.extend(["", "Examples:", ""])
        for example in change["examples"]:
            lines.append(f"- `{example['identity']}`: {example['description']}")
            lines.append(f"  - Evidence: {citation_text(example['evidence_refs'])}.")
        lines.append("")
    lines.extend(["## Remediation decision evidence", ""])
    lines.append(
        "Each verdict below refers to one of these packets. The semantic inventory is visible without opening source, "
        "and the expandable appendix contains the exact frozen patch or trace fragments covered by the packet."
    )
    lines.append("")
    for packet in report["decision_evidence_packets"]:
        append_decision_evidence_packet(lines, packet)
    packet_by_id = {packet["id"]: packet for packet in report["decision_evidence_packets"]}
    lines.extend(["## Recommended remediation", ""])
    for option in report["remediation_options"]:
        recommendation_label = " — selected recommendation" if option["role"] == report["recommendation"] else ""
        lines.extend([f"### {option['title']}{recommendation_label}", "", option["summary"], "", "Actions:", ""])
        lines.extend(f"- {action}" for action in option["actions"])
        lines.extend(["", "Concrete decision units:", ""])
        for unit in option["decision_units"]:
            packet = packet_by_id[unit["evidence_packet"]]
            lines.extend([f"#### `{unit['id']}` — {unit['title']}", "", "Artifacts or statements:", ""])
            lines.extend(f"- `{artifact}`" for artifact in unit["artifacts"])
            lines.extend(
                [
                    "",
                    "Changes covered by this verdict:",
                    "",
                ]
            )
            lines.extend(f"- `{change['id']}` — {change['title']}" for change in packet["changes"])
            lines.extend(
                [
                    "",
                    f"Decision evidence: [view the complete `{packet['id']}` packet](#decision-evidence-{packet['id']}).",
                ]
            )
            lines.extend(["", "Retain:", ""])
            lines.extend(f"- {item}" for item in unit["retain"] or ["Nothing in this unit under this option."])
            lines.extend(["", "Remove or restore:", ""])
            lines.extend(
                f"- {item}" for item in unit["remove_or_restore"] or ["No automatic removal or restoration in this unit."]
            )
            lines.extend(["", "Decision requested:", ""])
            lines.extend(
                f"- {item}" for item in unit["requires_decision"] or ["No further semantic decision in this unit."]
            )
            lines.extend(
                [
                    "",
                    "If you enter `Approved`:",
                    "",
                ]
            )
            lines.extend(f"- {item}" for item in unit["approved_means"])
            lines.extend(
                [
                    "",
                    "If you enter `Reject`:",
                    "",
                ]
            )
            lines.extend(f"- {item}" for item in unit["rejected_means"])
            lines.extend(
                [
                    "",
                    "If you enter `Question/Comment`, no remediation choice is recorded until the question is resolved.",
                    "",
                    "**User Verdict:** `[Approved / Reject / Question/Comment]`",
                    "",
                    "**User Question/Comment:** `[Type here]`",
                    "",
                    f"Why this boundary: {unit['reason']}",
                    "",
                    f"Evidence: {citation_text(unit['evidence_refs'])}.",
                    "",
                ]
            )
        lines.extend(["", "Reasons:", ""])
        lines.extend(f"- {reason}" for reason in option["reasons"])
        lines.extend(["", "Risks and tradeoffs:", ""])
        lines.extend(f"- {risk}" for risk in option["risks"])
        lines.append("")
    lines.extend(["## Evidence and reproducibility", ""])
    lines.append(f"- Manifest: `{display_path(manifest_path)}` with SHA-256 `{manifest_hash}`.")
    for item in verified:
        lines.append(f"- `{item['id']}`: `{item['path']}` with SHA-256 `{item['sha256']}`; {item['role']}")
    lines.extend(["", "## Limits", ""])
    lines.extend(f"- {item}" for item in report["limits"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    """Validate frozen evidence, compute statistics, and write both report forms."""
    arguments = parse_args()
    manifest_path = arguments.manifest.expanduser().resolve(strict=True)
    try:
        manifest_value = load_json(manifest_path)
        manifest = require_object(manifest_value, "manifest")
        require_exact_keys(manifest, TOP_LEVEL_REQUIRED, set(), "manifest")
        if manifest["schema_version"] != 4:
            raise AssessmentInputError("manifest.schema_version: expected 4")
        evidence, verified = load_evidence(manifest, manifest_path)
        evidence_ids = set(evidence)
        report = validate_report(manifest["report"], evidence, evidence_ids)
        levels = validate_levels(manifest["qualification_levels"], evidence, evidence_ids)
        manifest_hash = sha256_file(manifest_path)
        derived = {
            "schema_version": 4,
            "manifest": {"path": display_path(manifest_path), "sha256": manifest_hash},
            "evidence_inputs": verified,
            "qualification_levels": levels,
            "headline_facts": report["headline_facts"],
            "decision_evidence_packets": report["decision_evidence_packets"],
            "remediation_options": report["remediation_options"],
            "recommendation": report["recommendation"],
        }
        markdown = render_markdown(report, levels, verified, manifest_path, manifest_hash)
        atomic_write_text(arguments.output_json.expanduser(), canonical_json(derived))
        atomic_write_text(arguments.output_markdown.expanduser(), markdown)
    except (AssessmentInputError, OSError) as error:
        raise SystemExit(str(error)) from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
