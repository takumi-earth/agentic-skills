# Typed Outcome Assertions

## Decision table

| Current shape | Preferred action |
|---|---|
| Meaningful `Eq`/`PartialEq`; all fields are contractual | Compare the complete expected outcome |
| Equality includes nondeterministic or unrelated fields | Use an existing typed domain projection |
| New getter would exist only for one test | Do not add or call it; assert through the owning type |
| Getter has a real downstream reporting consumer | Preserve the getter and test the consumer contract |
| Expected construction repeats with real semantic meaning | Extract a shared test-owned constructor |
| Helper would only dodge a lint or coverage arm | Do not create it |

## Complete-outcome example

If a two-round outcome owns round identity, stage, exclusions, upgrade, and update effects, compare the complete two-element outcome collection when the test promises all of those facts. Mapping only `.stage()` can weaken the oracle and make the accessor a test-only single call.

## Counterexamples

- Do not compare a complete type containing timestamps, randomized identifiers, or diagnostic-only ordering unless those fields are contractual.
- Do not delete a public accessor merely because no in-repository consumer exists when a supported external contract is evidenced.
- Do not add `#[allow(clippy::single_call_fn)]` unless repository policy permits the exact site and a real consumer contract justifies the abstraction.

