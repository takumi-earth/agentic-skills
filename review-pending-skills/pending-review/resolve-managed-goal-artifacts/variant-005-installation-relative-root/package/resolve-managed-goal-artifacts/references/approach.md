# Approach contract

## Identity

- Candidate: `resolve-managed-goal-artifacts`
- Variant: `variant-005-installation-relative-root`
- Classification: `resource-gap`

## Required behavior

Preserve an installation-relative root contract by registering or executing the hook only from a real harness package location.

Use the lexical installed package location to identify the harness root and forbid resolved canonical-source execution. Mark the design as topology-sensitive and require deployment validation before use.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `references/installation-topology-contract.md`

## Relationships

- `auto-skill-enhancer`: `possible-enhancement-owner`
- `maintain-living-goal`: `goal-file-consumer`
- `define-codex-goal-artifacts`: `typed-contract-alternative`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- real copied installation
- relative and absolute symlink projections
- canonical-direct registration negative
- custom harness root negative

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit with every other candidate produced by this invocation; do not commit variants separately.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
