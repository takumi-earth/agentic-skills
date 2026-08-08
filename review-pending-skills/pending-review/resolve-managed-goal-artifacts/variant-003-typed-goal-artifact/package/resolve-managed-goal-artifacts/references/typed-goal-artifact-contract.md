# Typed Goal Artifact Contract

Use this reference only for `resolve-managed-goal-artifacts/variant-003-typed-goal-artifact`.

## Contract

Read a versioned managed_objective_artifacts list from the successful goal response, require exactly one supported file for the completion handoff, validate its containment and existence, and use objective prose only for human display.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- zero, one, and multiple artifact records
- legacy objective-only response
- resume serialization
- pasted text and future non-text artifact kinds

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
