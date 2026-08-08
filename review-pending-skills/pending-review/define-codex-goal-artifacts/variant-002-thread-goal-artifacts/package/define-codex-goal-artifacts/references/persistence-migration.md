# Persistence Migration

Use this reference only for `define-codex-goal-artifacts/variant-002-thread-goal-artifacts`.

## Contract

Add a versioned artifact list to internal goal state and protocol ThreadGoal, preserve it across update, pause, resume, and completion, and expose it in tool responses without changing human objective text.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- goal create/update response
- resume persistence
- legacy serialized state
- multiple artifact kinds
- deleted artifact behavior

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
