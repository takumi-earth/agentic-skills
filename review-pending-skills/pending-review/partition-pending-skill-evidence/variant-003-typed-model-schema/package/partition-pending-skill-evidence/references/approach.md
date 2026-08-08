# Approach contract

## Identity

- Candidate: `partition-pending-skill-evidence`
- Variant: `variant-003-typed-model-schema`
- Classification: `instruction-gap`, `resource-gap`

## Required behavior

Define evidence records as a typed model and generate JSON Schema into the owning pending variant.

Keep one typed source model, generate deterministic JSON Schema as a product resource, validate scratch evidence instances against it without relocating them, and fail when generated schema drifts from the typed model.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `scripts/generate_evidence_schema.py`
- `references/evidence-record.schema.json`
- `references/schema-generation-contract.md`

## Relationships

- `auto-skill-creator`: `possible-enhancement-owner`
- `review-pending-skills`: `pending-store-owner`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- deterministic schema generation
- schema drift detection
- valid and invalid evidence instances
- home-relative path constraint

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit. Keep the move manifest and run evidence in scratch; move only reusable resources declared by the manifest.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
