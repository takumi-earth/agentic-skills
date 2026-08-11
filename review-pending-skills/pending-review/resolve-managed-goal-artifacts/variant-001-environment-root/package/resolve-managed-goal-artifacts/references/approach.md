# Approach contract

## Identity

- Candidate: `resolve-managed-goal-artifacts`
- Variant: `variant-001-environment-root`
- Classification: `resource-gap`

## Required behavior

Treat inherited `CODEX_HOME` as the authoritative runtime root and fall back to `~/.codex` only when the variable is absent.

Reject empty and unusable configured roots. Use objective prose only to identify candidate references, never to establish the trusted root. Resolve exactly one filename- and extension-agnostic `attachments/<uuid>/<filename>` regular non-symlink file after canonical containment and symlink-escape checks. Return a pure typed result and keep hook-envelope rendering outside the resolver.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `scripts/resolve_goal_artifact.py`
- `references/resolution-contract.md`

## Relationships

- `maintain-living-goal`: `canonical-owner`
- `auto-skill-enhancer`: `downstream-consumer`
- `define-codex-goal-artifacts`: `typed-contract-alternative`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- custom CODEX_HOME positive fixture
- unset CODEX_HOME ~/.codex fallback fixture
- invalid configured root and non-text objective negatives
- zero, one, and multiple managed references
- invalid UUID, traversal, non-file, direct-symlink, and symlink-escape negatives
- repeat-call determinism and filename/extension independence

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit with every other candidate produced by this invocation; do not commit variants separately.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
