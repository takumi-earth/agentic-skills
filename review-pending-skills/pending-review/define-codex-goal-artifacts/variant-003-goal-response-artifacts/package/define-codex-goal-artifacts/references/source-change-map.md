# Source Change Map

Use this reference only for `define-codex-goal-artifacts/variant-003-goal-response-artifacts`.

## Contract

Derive and attach managed artifact metadata at goal-tool response construction, pass it unchanged through PostToolUse, and document that it is event-local rather than durable goal state.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- create and update tool response
- PostToolUse pass-through
- resume without prior response
- compatibility with clients deserializing ThreadGoal

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
