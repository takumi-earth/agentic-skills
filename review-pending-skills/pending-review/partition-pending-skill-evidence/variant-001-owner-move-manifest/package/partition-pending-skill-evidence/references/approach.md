# Approach contract

## Identity

- Candidate: `partition-pending-skill-evidence`
- Variant: `variant-001-owner-move-manifest`
- Classification: `instruction-gap`, `resource-gap`

## Required behavior

Assign each reusable resource to one owning variant and move pre-existing scratch resources through a validated source-to-destination manifest.

Classify every artifact as evidence instance or reusable contract, require source existence and destination absence, create all candidate destinations first, execute mv exactly once per resource, verify hashes and empty source slots, and update provenance without moving evidence instances.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `scripts/move_pending_resources.py`
- `scripts/run_home_normalized_skill_guard.py`
- `references/evidence-record.schema.json`
- `references/move-resource-manifest.schema.json`
- `references/scope-guard-adapter.md`
- `references/storage-boundary.md`

## Relationships

- `auto-skill-creator`: `possible-enhancement-owner`
- `review-pending-skills`: `pending-store-owner`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- positive multi-resource move
- missing source
- existing destination
- escaping destination
- duplicate source owner
- hash mismatch
- evidence-instance exclusion

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit. Keep the move manifest and run evidence in scratch; move only reusable resources declared by the manifest.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
