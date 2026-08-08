# Approach contract

## Identity

- Candidate: `resolve-managed-goal-artifacts`
- Variant: `variant-003-typed-goal-artifact`
- Classification: `resource-gap`

## Required behavior

Carry managed objective artifacts as typed goal-response data and stop recovering them from prose.

Read a versioned managed_objective_artifacts list from the successful goal response, require exactly one supported file for the completion handoff, validate its containment and existence, and use objective prose only for human display.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `references/typed-goal-artifact-contract.md`
- `references/migration-and-resume.md`

## Relationships

- `auto-skill-enhancer`: `possible-enhancement-owner`
- `maintain-living-goal`: `goal-file-consumer`
- `define-codex-goal-artifacts`: `typed-contract-alternative`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- zero, one, and multiple artifact records
- legacy objective-only response
- resume serialization
- pasted text and future non-text artifact kinds

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit with every other candidate produced by this invocation; do not commit variants separately.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
