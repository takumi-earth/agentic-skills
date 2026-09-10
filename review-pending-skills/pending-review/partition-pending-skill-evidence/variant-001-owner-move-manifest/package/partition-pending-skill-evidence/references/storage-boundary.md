# Storage Boundary

Use this reference only for `partition-pending-skill-evidence/variant-001-owner-move-manifest`.

## Contract

Classify artifacts as evidence instances or reusable resources. Require the declared candidate and variant to exist completely, validate the selected source without following symlinks, publish verified bytes without replacing a destination, remove only the unchanged selected source, and report completed, partial, and remaining effects. Update task-required provenance without moving evidence instances.

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

## Executable boundary

Manifest records require `candidate_name` and `variant_id` in addition to source, destination, hash, and reusable-resource classification. Relative paths use `--repo` as their base. The destination must lie inside that exact complete variant, and `review.json` must agree with its declared identity. Reject symlinks in selected path components before resolving another object. Validation records source filesystem identity; it is not a portable authorization token.

The mover copies the opened source into a temporary file beside the destination, verifies the hash, publishes it with exclusive hard-link creation, rechecks source identity and bytes, then removes the source. A late destination is preserved. This supports cross-filesystem source transfers, provided the destination filesystem supports hard links. No replacement fallback is allowed. The helper cleans up only its temporary file and retains published effects on failure; it does not promise an atomic batch or crash-durable recovery log.

The CLI returns `2` with a structured `invalid-manifest` failure before execution, or `3` with a `move-failed` result during execution. `moved` lists completed verified moves; `partial` identifies the current published effect and whether the source was removed; `remaining` excludes a partially applied record. Reconcile partial effects before any authorized recovery, and never blindly replay the batch. Path and identity checks do not lock the filesystem against concurrent writers; execute only with control of the selected source and destination directories.
