---
name: assert-complete-typed-outcomes
description: "Resolve strict Rust test assertions that make a production accessor, discriminator, or projection single-use solely for test convenience. Use during `$implement-strict-work` when Clippy reports `single_call_fn` or dead-code pressure after a new test call, when a typed outcome already has meaningful equality, or when a test-only classifier is being considered. Prefer complete domain-owned typed evidence without suppressing lints or changing public APIs. Do not force whole-value equality when fields are nondeterministic or outside the behavior contract."
---

# Assert Complete Typed Outcomes

Keep the assertion at the strongest existing typed behavior boundary.

Use `$guard-strict-work` and `$implement-strict-work` for authority and source edits. Read [the typed outcome reference](references/typed-outcome-assertions.md) when a test creates the only call to a production projection.

## Diagnose the call

1. Identify every real consumer of the accessor or projection.
2. Determine whether it is a supported public/reporting contract, a dormant extension seam, or test convenience.
3. Inspect the complete outcome type, its `Eq` or `PartialEq` meaning, constructors, and established test vocabulary.
4. Decide which fields are behavior and which are incidental or nondeterministic.

## Choose the semantic oracle

- Compare the complete typed outcome when its equality contract matches the behavior under test.
- Use an existing domain projection when full equality would pin unrelated state.
- Extract a test-owned expected-value helper only when it names reusable domain vocabulary and has multiple real callers.
- Preserve a production accessor when a real downstream consumer contract exists.
- Do not add an accessor, classifier enum, discriminant helper, or lint exception solely to make one assertion convenient.

## Resolve structurally

Strengthen the test rather than muting the warning. A complete outcome comparison can prove identity, stage or attribution, exclusions, and effects together when all are contractual.

Do not claim the warning cleared until an authorized lint command runs. Keep source remediation, assertion results, process exit status, and canonical verification separate.

