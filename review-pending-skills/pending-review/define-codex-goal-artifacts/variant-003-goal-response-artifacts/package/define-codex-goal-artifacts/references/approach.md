# Approach contract

## Identity

- Candidate: `define-codex-goal-artifacts`
- Variant: `variant-003-goal-response-artifacts`
- Classification: `not-a-skill-issue`, `speculative architecture candidate`

## Required behavior

Attach versioned `managedObjectiveArtifacts` only to the selected `GoalToolResponse` profile; keep durable artifact state unchanged.

Read `goal-tool-response-schema.md` for the trusted invocation input, exact fields, current/event binding, and unavailable-after-resume behavior. Read `source-change-map.md` for revision-attributed integration seams. A response sidecar does not remove prose parsing unless its producer has an independent authoritative designation.

## Resources

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

Use the interactive review owner's complete candidate-root commit contract for an authorized correction. Automatic creation retains its invocation-wide commit rule. This specification does not authorize editing `~/rust-forks/codex-orig`.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
