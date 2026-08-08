# Structured Failure Exceptions

Use this reference only for `render-hook-decision-failures/variant-002-structured-failure-exceptions`.

## Contract

Define a bounded exception hierarchy carrying diagnostic fields, prevent broad exception text from becoming the public contract, and render unexpected exceptions separately from expected policy failures.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- expected exception conversion
- unexpected exception classification
- no stack trace in hook stdout
- exact field preservation

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
