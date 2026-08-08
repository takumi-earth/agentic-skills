# Approach contract

## Identity

- Candidate: `resolve-managed-goal-artifacts`
- Variant: `variant-002-hook-context-root`
- Classification: `resource-gap`

## Required behavior

Add a typed codex_home or attachments_root field to PostToolUse and prefer that event value over process environment.

Consume a versioned hook-context root supplied by Codex, validate it as the managed harness root, retain CODEX_HOME and ~/.codex only as backwards-compatible fallbacks, and report which authority source selected the root.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `references/codex-hook-context-contract.md`
- `references/compatibility-fallback.md`

## Relationships

- `auto-skill-enhancer`: `possible-enhancement-owner`
- `maintain-living-goal`: `goal-file-consumer`
- `define-codex-goal-artifacts`: `typed-contract-alternative`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- typed field preferred over conflicting environment
- old event schema environment fallback
- missing all authority sources
- cross-platform path serialization

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit with every other candidate produced by this invocation; do not commit variants separately.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
