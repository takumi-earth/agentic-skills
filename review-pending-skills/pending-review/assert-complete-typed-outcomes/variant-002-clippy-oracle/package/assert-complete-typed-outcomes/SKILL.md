---
name: assert-complete-typed-outcomes
description: "Triage Rust `single_call_fn`, `dead_code`, or analogous warnings caused when a test is the only caller of a production getter, discriminator, or projection. Use when the warning appears after adding an assertion and a complete typed outcome or existing domain projection may provide stronger evidence. Distinguish genuine public consumers from test convenience, refactor the oracle structurally, and keep post-fix verification explicit. Do not use for arbitrary Clippy warnings or force full equality over incidental fields."
---

# Assert Complete Typed Outcomes

Treat a test-created accessor warning as evidence about the assertion boundary.

## Trace the warning

- Confirm the test is the only call and identify whether the method was previously unused, newly added, or externally consumed.
- Read the complete owning type, constructors, equality semantics, reporting façades, and neighboring assertion patterns.
- Classify the accessor as a real contract, supported extension seam, or test-only projection.

## Select the cleanest assertion

Use this order:

1. Complete typed equality when every compared field is behavior.
2. An existing typed domain projection when full equality includes incidental state.
3. A genuine new comparison contract on the owning model when repeated behavior requires it.
4. A narrow reasoned lint exception only when repository policy permits it and a real consumer contract cannot be visible locally.

Never create a production getter, classifier, discriminant helper, or one-call wrapper solely for a test. Extract an expected-value helper only when it removes real repeated construction and names domain behavior.

## Preserve API and evidence boundaries

- Do not delete a deliberate public API based only on local reachability.
- Do not keep a ghost API merely because a test can call it once.
- Do not weaken the asserted behavior to silence the lint.
- Do not describe source inspection as a passing lint result.
- Rerun only the exact formatter or lint command authorized by the user or active workflow.

Report the structural cause, chosen typed boundary, public API disposition, and exact unrun or completed verification separately.

