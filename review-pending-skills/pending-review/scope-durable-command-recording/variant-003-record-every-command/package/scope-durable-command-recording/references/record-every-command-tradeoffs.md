# Record Every Command Tradeoffs

Use this reference only for `scope-durable-command-recording/variant-003-record-every-command`.

## Contract

Retain the overbroad approach as rejected comparison evidence, record its avoidable indirection and interface-drift cost, and prohibit it from controlling current execution.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- measure wrapper overhead
- reproduce unsupported-flag failure
- confirm pending inactive status

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
