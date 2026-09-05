# Typed Outcome Assertions

Keep assertions at the strongest existing typed boundary that observes the promised behavior. Use this reference when a test creates single-use or dead-code pressure on a production accessor, discriminator, or projection, or when a test-only classifier is being considered.

## Identify the contract

Trace the real consumers and distinguish a supported public/reporting contract, a supported dormant extension seam, and test convenience. Local absence alone does not establish that a public accessor is obsolete. Read the complete owning outcome type, constructors, equality semantics, and established test vocabulary before selecting the assertion.

The presence of `Eq` or `PartialEq` is not enough: determine whether equality observes every contractual field and whether it also pins incidental or nondeterministic state.

## Choose the assertion

| Current shape | Preferred action |
|---|---|
| Equality observes the complete contract and compares only contractual fields | Compare the complete expected typed outcome |
| Full equality includes nondeterministic or unrelated fields | Use an existing typed domain projection that observes the promised behavior |
| A new getter or classifier would exist solely for one test | Assert through the existing owning type without manufacturing a production API |
| A getter serves a real downstream reporting contract or supported extension seam | Preserve that contract; do not delete it based only on local reachability |
| Expected construction expresses repeated domain vocabulary with multiple real callers | Extract a test-owned expected-value helper |
| A helper or filler call would exist only to dodge a lint or coverage arm | Do not create it |

If a two-round outcome owns round identity, stage, exclusions, upgrade, and update effects, compare the complete two-element outcome collection when the test promises all of those facts. Mapping only `.stage()` can weaken the assertion and make the accessor a test-only single call.

Do not force whole-value equality over timestamps, randomized identifiers, or diagnostic-only ordering unless those fields are contractual. Do not weaken the promised behavior merely to avoid those fields.

## Preserve authority and evidence

Apply the implementation owner's public API and exception rules. A getter, classifier enum, discriminant helper, one-call wrapper, or lint exception is not justified solely by one convenient assertion. An exception still requires the current repository or user contract to authorize the exact site category with its semantic criteria; a supported external consumer does not grant that authority by itself.

Source remediation does not establish that the warning cleared. Report source changes, executed assertions, process exit, and canonical verification separately, using only the authorized evidence available.
