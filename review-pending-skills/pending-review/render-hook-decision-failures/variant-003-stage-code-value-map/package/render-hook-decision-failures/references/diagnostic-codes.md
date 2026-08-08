# Diagnostic Codes

Use this reference only for `render-hook-decision-failures/variant-003-stage-code-value-map`.

## Contract

Emit a concise diagnostic such as stage=resolve_goal_file, code=attachments_root_mismatch, condition=..., expected=..., received=... and keep value rendering home-relative.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- stable field ordering
- home-path normalization
- null and collection rendering
- no generic fallback when known values exist

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
