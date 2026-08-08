# Topology Fixture Matrix

Use this reference only for `validate-symlinked-skill-runtime/variant-002-deployment-topology-matrix`.

## Contract

Build disposable copied and symlinked package fixtures, run the same entry point and arguments in every topology, compare normalized outputs and side-effect paths, and fail with exact expected and received topology facts.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- positive parity fixture
- deliberate __file__ parent regression
- relative versus absolute symlink parity
- no mutation outside disposable fixtures

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
