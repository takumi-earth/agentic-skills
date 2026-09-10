# Approach contract

## Identity

- Candidate: `define-codex-goal-artifacts`
- Variant: `variant-002-thread-goal-artifacts`
- Classification: `not-a-skill-issue`, `speculative architecture candidate`

## Required behavior

Persist the versioned `managedObjectiveArtifacts` association on `ThreadGoal` and expose it through the selected native protocol.

Read `thread-goal-artifact-schema.md` for authoritative selection, roles, exact locators, and field semantics. Read `persistence-migration.md` for atomic objective revision changes, status preservation, legacy rows, fork/resume behavior, and the attributed source map. Preserve human objective text and independently owned status authority.

## Resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `references/thread-goal-artifact-schema.md`
- `references/persistence-migration.md`

## Relationships

- `~/rust-forks/codex-orig`: `authoritative-source-checkout`
- `resolve-managed-goal-artifacts`: `downstream-consumer`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- goal create/update response
- resume persistence
- legacy serialized state
- multiple artifact kinds
- deleted artifact behavior

## Git and activation boundary

Use the interactive review owner's complete candidate-root commit contract for an authorized correction. Automatic creation retains its invocation-wide commit rule. This specification does not authorize editing `~/rust-forks/codex-orig`.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
