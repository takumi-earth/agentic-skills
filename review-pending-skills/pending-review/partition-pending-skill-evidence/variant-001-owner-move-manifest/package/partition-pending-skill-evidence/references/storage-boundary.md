# Storage Boundary

Use this reference only for `partition-pending-skill-evidence/variant-001-owner-move-manifest`.

## Contract

Classify every artifact as evidence instance or reusable contract, require source existence and destination absence, create all candidate destinations first, execute mv exactly once per resource, verify hashes and empty source slots, and update provenance without moving evidence instances.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- positive multi-resource move
- missing source
- existing destination
- escaping destination
- duplicate source owner
- hash mismatch
- evidence-instance exclusion

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
