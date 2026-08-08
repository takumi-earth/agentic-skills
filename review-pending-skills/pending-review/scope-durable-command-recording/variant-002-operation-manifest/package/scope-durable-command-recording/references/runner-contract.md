# Runner Contract

Use this reference only for `scope-durable-command-recording/variant-002-operation-manifest`.

## Contract

Persist cwd, inputs, exact argv, expected conditions, outputs, and timeout before execution; keep passive reads outside the manifest; refuse shell interpolation and unlisted side effects.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- exact argv preservation
- home-path normalization
- undeclared output rejection
- passive read exemption
- nonzero diagnostic reporting

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
