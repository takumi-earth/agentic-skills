# Per Candidate Checkpoint Tradeoffs

Use this reference only for `persist-pending-creation-batches/variant-003-per-candidate-checkpoints`.

## Contract

Retain the superseded per-candidate checkpoint design for comparison, explicitly record the user's rejection and the fragmentation cost, and never execute it during the controlling grouped-commit workflow.

This is a comparison contract only. Do not stage, commit, or mutate a live batch through it.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- demonstrate commit-count growth
- compare recovery granularity
- confirm variant remains pending and inactive

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
