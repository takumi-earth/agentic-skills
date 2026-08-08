# Lexical Path Limitations

Use this reference only for `validate-symlinked-skill-runtime/variant-004-lexical-install-path`.

## Contract

Capture argv[0] or the registered command path before resolution and infer state only from an explicitly guaranteed installation layout. Mark the approach as weak because direct canonical registration and copied launchers invalidate it.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- registered symlink path
- PATH lookup
- direct script invocation
- renamed wrapper
- canonical registration negative

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
