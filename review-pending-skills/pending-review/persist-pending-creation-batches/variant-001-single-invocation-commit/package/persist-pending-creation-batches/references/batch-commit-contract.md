# Batch Commit Contract

Use this reference only for `persist-pending-creation-batches/variant-001-single-invocation-commit`.

## Contract

Validate all variants first, record the precommit OID, reject unrelated staged paths, stage every exact candidate root in one path-bounded command, require no candidate-root remainder, commit once, and require a one-commit transition before later edits.

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
- rename and copy status parsing
- index and worktree divergence
- single resulting commit
- multi-commit transition rejection

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
