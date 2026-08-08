# Objective Path Grammar

Use this reference only for `resolve-managed-goal-artifacts/variant-004-objective-path-validation`.

## Contract

Extract exact path tokens rather than enumerate sibling attachment directories, require an attachments/<uuid>/<file> shape, compare the inferred root with CODEX_HOME or ~/.codex, and reject mismatches with explicit expected and received values.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- exact current wrapper string
- spaces and punctuation in file names
- two path tokens
- root mismatch
- path traversal and symlink escape

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
