# Approach contract

## Identity

- Candidate: `partition-pending-skill-evidence`
- Variant: `variant-002-direct-owner-emission`
- Classification: `instruction-gap`, `resource-gap`

## Required behavior

Emit reusable schemas and product resources directly into their owning variants and reserve scratch exclusively for evidence instances.

Require candidate identity before resource creation, reject a reusable artifact whose destination is beneath scratch, and record candidate-relative resource paths in review metadata from the start.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `references/evidence-record.schema.json`
- `references/direct-emission-contract.md`

## Relationships

- `auto-skill-creator`: `possible-enhancement-owner`
- `review-pending-skills`: `pending-store-owner`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- direct candidate resource creation
- scratch resource rejection
- run evidence acceptance
- cross-candidate relationship reference

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit. Keep the move manifest and run evidence in scratch; move only reusable resources declared by the manifest.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
