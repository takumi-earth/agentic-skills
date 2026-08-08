# Hook Channel Contract

Use this reference only for `render-hook-decision-failures/variant-004-stderr-audit-and-context`.

## Contract

Render identical diagnostic facts to both channels without changing the hook exit status or contaminating stdout JSON. Explicitly mark that Codex may not surface successful-hook stderr, so additionalContext remains required.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- stdout parses independently
- stderr event contains matching diagnostic code
- exit zero remains non-blocking
- additionalContext remains actionable when stderr is discarded

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
