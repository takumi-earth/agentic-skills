# Source Change Map

Use this reference only for `define-codex-goal-artifacts/variant-001-post-tool-use-codex-home`.

## Contract

Extend hook schema construction at the runtime boundary, serialize the configured root home-relatively where appropriate, retain backwards compatibility for handlers that ignore the field, and document trust and platform semantics.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- schema serialization fixture
- old handler compatibility
- custom CODEX_HOME
- resume and fork event parity

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
