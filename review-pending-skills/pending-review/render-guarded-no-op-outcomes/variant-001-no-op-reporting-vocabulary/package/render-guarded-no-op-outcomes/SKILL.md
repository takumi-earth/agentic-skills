---
name: render-guarded-no-op-outcomes
description: "Explain guarded zero-write outcomes for filesystem, Git, remediation, migration, and reconciliation operations. Use when a guard matched and the desired state was already present, especially before reporting the shorthand guarded no-op to a user."
---

# Render Guarded No-Op Outcomes

Use plain language before shorthand:

> The guard matched, the target already had the desired state, and the operation performed zero writes. This is a successful guarded no-op.

## Require all three facts

Call an outcome a guarded no-op only when:

1. the named precondition or content guard matched;
2. the exact desired state was positively proven already present;
3. the operation performed zero writes.

Report the target, checked condition, expected value, received value, desired state, and write count. State separately whether later verification ran.

## Distinguish neighboring outcomes

- `write`: the guard matched and the operation changed one or more targets;
- `guarded no-op`: the guard matched, desired state was already present, and write count was zero;
- `blocked`: the guard did not match, so no write was attempted;
- `failed`: the operation encountered an error before reaching its promised result;
- `verified`: a separate postcondition check passed after a write or no-op.

Never call a failed guard a no-op. Never imply that zero writes mean a build, test, or repository gate passed.

## Check examples

Render an already-restored file, a mismatched guard, a successful deletion, a failed write, a no-op with verification deliberately unrun, and a no-op followed by a separate passed verification.
