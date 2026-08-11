# Topology Fixture Matrix

Use this reference only for `validate-symlinked-skill-runtime/variant-002-deployment-topology-matrix`.

## Contract

Build disposable copied, relative-symlink, and absolute-symlink fixtures around the canonical package. Run the target's real entry point and arguments in every topology, compare exit status and normalized output, validate declared side-effect containment, and prove the canonical package and runtime state remain unchanged.

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
- real entry-point output and declared side-effect parity
- unchanged canonical package and runtime state
- no mutation outside disposable fixtures

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
