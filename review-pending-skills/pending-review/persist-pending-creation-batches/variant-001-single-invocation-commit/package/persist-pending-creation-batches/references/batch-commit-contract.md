# Batch Commit Contract

Use this reference only for `persist-pending-creation-batches/variant-001-single-invocation-commit`.

## Contract

Validate all variants first, reject unrelated staged paths, stage the full root set in one path-bounded command, require no candidate-root remainder, commit once, and prohibit later edits until the initial batch commit exists.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- multiple complete candidate roots
- unrelated staged path
- missing declared root
- unstaged candidate remainder
- single resulting commit

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
