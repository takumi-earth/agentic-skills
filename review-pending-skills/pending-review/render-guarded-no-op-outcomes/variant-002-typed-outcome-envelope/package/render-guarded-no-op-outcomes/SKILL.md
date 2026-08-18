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

For `blocked`, the guard must be unmatched and write count zero. For `write`, the guard must match and write count must be positive. For `failed`, provide a nonempty error. For `verified`, provide a passed verification description.

The renderer emits JSON containing the validated outcome and one deterministic human sentence. It does not perform the mutation or verification.

## Preserve exact scope

Include the operation, target, checked condition, expected and received values, desired state, write count, and verification status. Redact secrets before constructing the envelope. Do not infer repository correctness from an operation-level result.

Validate every outcome, each invalid cross-field combination, zero and multiple writes, verification deliberately not run, special characters, and malformed input.
