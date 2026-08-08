# Compatibility Fallback

Use this reference only for `resolve-managed-goal-artifacts/variant-002-hook-context-root`.

## Contract

Consume a versioned hook-context root supplied by Codex, validate it as the managed harness root, retain CODEX_HOME and ~/.codex only as backwards-compatible fallbacks, and report which authority source selected the root.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- typed field preferred over conflicting environment
- old event schema environment fallback
- missing all authority sources
- cross-platform path serialization

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
