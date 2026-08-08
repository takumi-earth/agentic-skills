# Approach contract

## Identity

- Candidate: `define-codex-goal-artifacts`
- Variant: `variant-003-goal-response-artifacts`
- Classification: `not-a-skill-issue`, `speculative architecture candidate`

## Required behavior

Add managed artifacts only to GoalToolResponse to keep ThreadGoal stable.

Derive and attach managed artifact metadata at goal-tool response construction, pass it unchanged through PostToolUse, and document that it is event-local rather than durable goal state.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `references/goal-tool-response-schema.md`
- `references/source-change-map.md`

## Relationships

- `~/rust-forks/codex-orig`: `authoritative-source-checkout`
- `resolve-managed-goal-artifacts`: `downstream-consumer`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- create and update tool response
- PostToolUse pass-through
- resume without prior response
- compatibility with clients deserializing ThreadGoal

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit; do not edit ~/rust-forks/codex-orig during pending creation.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
