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
  "content_guards":{"src/example.rs":"sha256"},
  "restore_objects":{"blob-id":{"available":true,"sha256":"sha256"}},
  "effect_paths":["src/example.rs"],
  "index_preservation_capability":true,
  "head":"commit-id",
  "index_sha256":"sha256"
}
```

Run:

```bash
python3 scripts/compare_application_guards.py --before <before.json> --after <after.json>
```

The report classifies content, restore, effect-path, and index-preservation invariants. It reports changed `head` and `index_sha256` separately as representation changes and sets `application_ready` only when every application invariant matches and current index preservation remains available.

## Interpret narrowly

A ready report does not authorize application, reopen a verdict, or verify a repository. A blocked report must name the drifted invariant; do not replace it with a blanket re-audit. Never mutate Git while producing the comparison.

Validate representation-only change, target drift, restore availability drift, effect-path drift, lost index preservation, malformed input, and empty effect paths.
