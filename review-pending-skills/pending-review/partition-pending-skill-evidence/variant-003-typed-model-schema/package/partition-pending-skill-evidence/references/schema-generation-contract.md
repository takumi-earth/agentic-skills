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
