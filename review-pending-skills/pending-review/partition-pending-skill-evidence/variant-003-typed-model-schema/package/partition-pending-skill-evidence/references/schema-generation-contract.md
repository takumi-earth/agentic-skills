# Schema Generation Contract

Use this reference only for `partition-pending-skill-evidence/variant-003-typed-model-schema`.

## Contract

Keep one typed source model, generate deterministic JSON Schema as a product resource, validate scratch evidence instances against it without relocating them, and fail when generated schema drifts from the typed model.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- deterministic schema generation
- schema drift detection
- valid and invalid evidence instances
- home-relative path constraint

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.

## Authoritative model and executable interface

`EvidenceRecord` in `scripts/generate_evidence_schema.py` is the typed source: required fields use `Required`, the version uses `Literal`, and string constraints and path roles use `Annotated`. Schema properties and required fields derive from those annotations. `x-model-sha256` identifies the normalized model contract, so model changes alter generated output and its drift check.

- Generate the schema with `python3 scripts/generate_evidence_schema.py --output references/evidence-record.schema.json`.
- Compare it with the current model using the same command plus `--check`.
- Validate an existing evidence instance without modifying or moving it using `python3 scripts/generate_evidence_schema.py --validate <evidence.json>`.

`evidence` contains path strings. Only those designated fields normalize the current process's home prefix to `~`; outside-home paths, including similarly prefixed neighbors, retain identity. `condition`, `expected`, `received`, and extension fields may contain legitimate non-path strings and are preserved. Validation reports identify a normalized projection and its original input-byte hash; a normalization report does not claim the input file was rewritten.

The portable schema uses the custom `home-presented-path` format. External JSON Schema validators must register a format checker that accepts only strings unchanged by `presented_path`; schema parsing without that checker does not enforce the runtime-home rule. Direct `validate_instance` checks canonical input, while the CLI normalizes only designated path fields in memory before validating. Generation and validation install nothing and authorize no extra ledger.

Exit `0` means generation/checking or instance validation succeeded; `1` means schema drift or invalid evidence; `2` means malformed input or an operational failure. Diagnostics and CLI path fields use `~/...`. The runtime uses the standard library; the packaged comparison tests also use `jsonschema`.
