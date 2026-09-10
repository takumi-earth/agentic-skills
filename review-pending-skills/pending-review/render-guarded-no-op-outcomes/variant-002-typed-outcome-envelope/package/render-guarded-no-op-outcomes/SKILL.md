---
name: render-guarded-no-op-outcomes
description: "Validate and render typed guarded-mutation outcomes for write, no-op, blocked, failed, and verified states. Use when a command or remediation workflow needs machine-readable result invariants and a deterministic human explanation of whether any write occurred."
---

# Render Guarded No-Op Outcomes

Use the schema in `references/guarded-outcome.schema.json` and the bundled renderer to keep human and machine meanings aligned.

## Render one outcome

Run:

```bash
python3 scripts/render_guarded_outcome.py --input <outcome.json>
```

For `no-op`, the renderer requires:

- `guard.matched` to be `true`;
- `desired_state.proven` to be `true`;
- `write_count` to be `0`.

For `blocked`, the guard must be unmatched and completed write count zero; this count alone says nothing about attempted writes. For `write`, the guard must match and completed write count must be positive. For `failed`, provide a nonempty error and the actual completed write count, including partial effects. Non-failed application outcomes require `error: null`.

For `verified`, supply `application_outcome` (`write`, `no-op`, `blocked`, or `failed`) and a passed verification description. Apply the underlying outcome's same invariants. Other outcomes omit `application_outcome`; their `verification` field independently records `not-run`, `passed`, or `failed`. Verification can confirm a blocked or failed result without converting that application result into success.

All declared fields are required, with unknown fields rejected at each object level. Conditions and identifying descriptions must contain non-whitespace text. Expected and received strings preserve legitimate empty observations. Passed or failed verification requires a description; `not-run` may have an empty description. The schema and CLI enforce the same outcome conditions.

The renderer emits JSON containing the normalized outcome, its deterministic human explanation, and `input_sha256` for the exact parsed input bytes. Every explanation includes the application result, actual write count, guard observations, desired-state description and proof claim, verification, and any error. A valid render exits `0` even when the reported operation failed; invalid input exits `2`. It performs no mutation, verification, or durable recording.

## Preserve exact scope

Include the operation, target, checked condition, expected and received values, desired state, write count, and verification status. Redact secrets before constructing the envelope. Do not infer repository correctness from an operation-level result.

Validate every outcome, each invalid cross-field combination, zero and multiple writes, verification deliberately not run, special characters, and malformed input.
