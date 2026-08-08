# Approach contract

## Identity

- Candidate: `resolve-managed-goal-artifacts`
- Variant: `variant-001-environment-root`
- Classification: `resource-gap`

## Required behavior

Treat CODEX_HOME as the authoritative runtime root and fall back to ~/.codex only when it is unset.

Read CODEX_HOME from the inherited hook environment, expand and canonicalize it, resolve only exact regular files under its attachments directory, reject ambiguity and symlink escape, and return a typed result naming condition, expected root, received root, candidate count, and candidate path.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `scripts/resolve_goal_artifact.py`
- `references/resolution-contract.md`

## Relationships

- `auto-skill-enhancer`: `possible-enhancement-owner`
- `maintain-living-goal`: `goal-file-consumer`
- `define-codex-goal-artifacts`: `typed-contract-alternative`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- custom CODEX_HOME positive fixture
- unset CODEX_HOME ~/.codex fallback fixture
- missing, ambiguous, invalid UUID, non-file, and symlink-escape negatives
- canonical-direct, copied, and symlinked package execution parity

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit with every other candidate produced by this invocation; do not commit variants separately.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
