# Approach contract

## Identity

- Candidate: `define-codex-goal-artifacts`
- Variant: `variant-002-thread-goal-artifacts`
- Classification: `not-a-skill-issue`, `speculative architecture candidate`

## Required behavior

Persist managed objective artifacts on ThreadGoal state and protocol events.

Add a versioned artifact list to internal goal state and protocol ThreadGoal, preserve it across update, pause, resume, and completion, and expose it in tool responses without changing human objective text.

## Planned resources

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

Include the complete candidate root in the single creation-batch commit; do not edit ~/rust-forks/codex-orig during pending creation.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
