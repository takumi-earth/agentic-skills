# Approach contract

## Identity

- Candidate: `validate-symlinked-skill-runtime`
- Variant: `variant-003-declared-runtime-context`
- Classification: `instruction-gap`, `resource-gap`

## Required behavior

Declare required runtime authorities in package metadata and have launchers inject them explicitly.

Define a small context manifest listing CODEX_HOME, canonical skill repository, scratchpad root, and package root ownership; validate required values before entry-point execution; do not infer missing values by walking parents.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `references/runtime-context.schema.json`
- `references/launcher-contract.md`

## Relationships

- `link-agentic-skills`: `deployment-owner`
- `filesystem-git-observability`: `filesystem-evidence-owner`
- `resolve-managed-goal-artifacts`: `current-regression-example`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- complete manifest
- missing authority
- conflicting environment and manifest
- schema version skew

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
