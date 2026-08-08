# Resolution Contract

Use this reference only for `resolve-managed-goal-artifacts/variant-001-environment-root`.

## Contract

Read CODEX_HOME from the inherited hook environment, expand and canonicalize it, resolve only exact regular files under its attachments directory, reject ambiguity and symlink escape, and return a typed result naming condition, expected root, received root, candidate count, and candidate path.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- custom CODEX_HOME positive fixture
- unset CODEX_HOME ~/.codex fallback fixture
- missing, ambiguous, invalid UUID, non-file, and symlink-escape negatives
- canonical-direct, copied, and symlinked package execution parity

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
