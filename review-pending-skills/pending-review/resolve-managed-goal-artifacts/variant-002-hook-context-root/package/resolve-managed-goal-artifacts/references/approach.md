# Approach contract

## Identity

- Candidate: `resolve-managed-goal-artifacts`
- Variant: `variant-002-hook-context-root`
- Classification: `resource-gap`

## Required behavior

Consume the paired `codex-runtime-context/v1` producer profile; prefer its valid bound root over process environment.

Read `codex-hook-context-contract.md` for exact schema, trusted profile binding, path modes, and the shared resolver owner. Read `compatibility-fallback.md` for the full absent/invalid/conflict matrix. Only declared legacy absence permits environment/default fallback; exact user-designated paths remain independently supported.

## Resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `references/codex-hook-context-contract.md`
- `references/compatibility-fallback.md`

## Relationships

- `auto-skill-enhancer`: `shared-resolver-consumer`
- `maintain-living-goal`: `shared-resolution-owner`
- `define-codex-goal-artifacts`: `typed-contract-alternative`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- typed field preferred over conflicting environment
- old event schema environment fallback
- missing all authority sources
- cross-platform path serialization

## Git and activation boundary

Use the interactive review owner's complete candidate-root commit contract for authorized corrections. The automatic creator's invocation-wide rule applies only to automatic creation.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
