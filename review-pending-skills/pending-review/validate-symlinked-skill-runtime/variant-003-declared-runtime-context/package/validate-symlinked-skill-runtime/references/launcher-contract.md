# Launcher Contract

Use this reference only for `validate-symlinked-skill-runtime/variant-003-declared-runtime-context`.

## Contract

Define a small context manifest listing CODEX_HOME, canonical skill repository, scratchpad root, and package root ownership; validate required values before entry-point execution; do not infer missing values by walking parents.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- complete manifest
- missing authority
- conflicting environment and manifest
- schema version skew

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
