---
name: enforce-adaptive-transform-tests
description: "Design or review typed test harnesses for adaptive parsed-source transformations. Use when helpers expose rendered source, parser nodes, tokens, debug serialization, or raw strings that make substring, regex, equality, snapshot, or copied-body assertions easy. Keep exact text tests only in a separately documented text-contract layer."
---

# Enforce Adaptive Transform Tests

Make the semantic oracle available and the textual shortcut unavailable by construction.

## Expose an opaque result

Return a typed result containing outcome, semantic delta, changed paths, and an opaque structural-query workspace. Do not expose raw source, token streams, unrestricted parser nodes, serialization, debug rendering, `Display`, `Deref<str>`, `AsRef<str>`, or a convenience render method.

Read [the opaque harness contract](references/opaque-harness-contract.md) before introducing or reviewing a helper API.

## Query semantic owners

Provide typed operations for declarations, implementations, calls, arguments, fields, arms, candidate identities, cardinality, failed predicates, and replay deltas. Assert that the intended owner changed, an equal-looking decoy did not, unrelated structure remained attached to its owner, and every non-applying outcome left the complete workspace unchanged.

## Separate evidence layers

- Use minimal version-neutral fixtures for primitives.
- Test registration and wiring by typed transformation ID.
- Apply movement, extension, decoy, ambiguity, drift, post-state, and replay variations through the same oracle.
- Exercise substantive behavior at the real product owner.
- Isolate legitimate wire, CLI, diagnostic, or generated-text contracts.

Use compile-fail or API-shape tests where practical to prove raw-string assertion APIs cannot accept the structural result. Treat newly written but unexecuted tests as implementation, not passing evidence.
