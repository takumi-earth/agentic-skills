# Approach contract

## Identity

- Candidate: `resolve-managed-goal-artifacts`
- Variant: `variant-003-typed-goal-artifact`
- Classification: `resource-gap`

## Required behavior

Consume exact typed goal-artifact data from one explicitly selected durable or response-only producer profile.

Read `typed-goal-artifact-contract.md` for the paired versioned schemas, verified attribution, role/cardinality rules, and exact locator modes. Read `migration-and-resume.md` for explicit legacy fallback and the distinct producer lifetimes. Invalid typed authority never triggers a prose fallback.

## Resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `references/typed-goal-artifact-contract.md`
- `references/migration-and-resume.md`

## Relationships

- `auto-skill-enhancer`: `shared-resolver-consumer`
- `maintain-living-goal`: `shared-resolution-owner`
- `define-codex-goal-artifacts`: `typed-contract-alternative`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- zero, one, and multiple artifact records
- legacy objective-only response
- resume serialization
- pasted text and future non-text artifact kinds

## Git and activation boundary

Use the interactive review owner's complete candidate-root commit contract for authorized corrections. The automatic creator's invocation-wide rule applies only to automatic creation.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
