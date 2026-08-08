# Path Authority Model

Use this reference only for `validate-symlinked-skill-runtime/variant-001-explicit-runtime-root`.

## Contract

Classify every path dependency as package, harness state, repository, or task output; reject scripts that derive a harness-state root from a resolved package parent; prefer env-selected executables and home-relative persisted paths.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- copied package
- relative symlink
- absolute symlink
- canonical-direct execution
- custom CODEX_HOME
- no hard-coded /usr/bin interpreter

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
