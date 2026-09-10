---
name: preserve-application-readiness-across-git-representation-change
description: "Compare two guarded-remediation evidence snapshots and classify invariant drift separately from Git representation changes. Use when HEAD, staging, or index identity changed after an application packet was prepared and a deterministic read-only readiness report is warranted."
---

# Preserve Application Readiness Across Git Representation Change

Use the bundled comparator only with evidence snapshots whose provenance and capture authority are already established.

## Prepare snapshots

Each JSON input must contain:

```json
{
  "content_guards":{"src/example.rs":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
  "restore_objects":{"blob-id":{"available":true,"sha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}},
  "effect_paths":["src/example.rs"],
  "operations":{"src/example.rs":{"id":"restore-example","kind":"restore","restore_object":"blob-id"}},
  "index_preservation_capability":true,
  "recovery_requirements":{"method":"preserve-current-index","exact_head":false,"exact_index":false},
  "head":"commit-id",
  "index_sha256":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
}
```

Run:

```bash
python3 scripts/compare_application_guards.py --before <before.json> --after <after.json>
```

Each ordered effect path needs a content guard and exactly one operation with a unique nonempty ID. Content guards are SHA-256 digests or `null` for expected absence. A `restore` operation names an existing restore record with a valid byte digest and explicit Boolean availability. A `delete` operation uses `restore_object: null`; deletion-only snapshots may have an empty `restore_objects` map.

The report compares content, ordered effects, operation identity, replacement bytes, and the declared recovery method. Current replacement availability and index-preservation capability must be true. `head` and `index_sha256` changes remain separately visible; they also block when the recovery contract requires exact identity. Matching unavailable or malformed inputs cannot produce readiness. A newly available replacement can satisfy the same byte identity without changing the selected operation.

`application_ready` means only that the supplied invariant claims meet these checks. `assessment_basis`, `independently_verified: false`, and `authorization_checked: false` preserve that limit. This helper never inspects actual target bytes, Git objects, or method capability and cannot establish them from caller labels.

## Interpret narrowly

A ready report does not authorize application, reopen a verdict, or verify a repository. A blocked report must name the drifted invariant; do not replace it with a blanket re-audit. Never mutate Git while producing the comparison.

Validate representation-only change, target drift, restore availability drift, effect-path drift, lost index preservation, malformed input, and empty effect paths.
