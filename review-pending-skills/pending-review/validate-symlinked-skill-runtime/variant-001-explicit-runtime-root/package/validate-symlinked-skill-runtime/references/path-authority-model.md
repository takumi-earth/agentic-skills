# Path Authority Model

Use this reference only for `validate-symlinked-skill-runtime/variant-001-explicit-runtime-root`.

## Contract

Classify every path dependency as package, harness state, repository, or task output. Require harness state explicitly, reserve `__file__` for package resources, and run the target's real entry point to prove that it observes the same runtime state across topologies. Require all task output beneath a disposable selected root.

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
- missing runtime authority and resolved-parent regression
- real entry-point output and side-effect containment
- no hard-coded /usr/bin interpreter

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
