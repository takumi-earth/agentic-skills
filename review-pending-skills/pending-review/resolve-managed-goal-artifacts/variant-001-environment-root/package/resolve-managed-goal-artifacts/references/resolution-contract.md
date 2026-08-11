# Resolution Contract

Use this reference only for `resolve-managed-goal-artifacts/variant-001-environment-root`.

## Contract

Read inherited `CODEX_HOME`, falling back to `~/.codex` only when the variable is absent. Reject an empty or unusable configured root. Use objective prose only to identify path references; require exactly one canonical regular non-symlink `attachments/<uuid>/<filename>` artifact beneath the trusted root. Return a deterministic typed result and make no writes or hook-envelope decisions.

Use success code `resolved-exact-artifact`. Use failure codes `invalid-runtime-root`, `objective-not-text`, `no-managed-artifact-reference`, `ambiguous-managed-artifacts`, `attachments-root-mismatch`, `managed-path-shape`, and `artifact-not-file`.

## Required evidence

- Record the exact condition being evaluated.
- Record the expected authority, value, or state.
- Record the received authority, value, or state.
- Preserve home-relative paths as `~/...` in persisted output.
- Distinguish a diagnostic nonzero exit from a passing assertion set.

## Validation

- custom CODEX_HOME positive fixture
- unset CODEX_HOME ~/.codex fallback fixture
- empty and unusable CODEX_HOME negatives
- non-text, zero-reference, and ambiguous-reference negatives
- invalid UUID, traversal, non-file, direct-symlink, and symlink-escape negatives
- repeat-call determinism and filename/extension independence

## Scope

Do not use this reference to activate the pending package or mutate any related official owner.
