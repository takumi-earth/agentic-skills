# Guard comparison-report variant

## Concrete intent

Compare two guarded-application evidence snapshots and report whether only Git representation changed or a real application invariant drifted.

## Approach

Use a deterministic, read-only JSON comparator for content guards, restore objects, effect paths, index-preservation capability, HEAD, and index identity. Keep representation changes in a separate result field.

## Preserved nuance

The comparator consumes supplied evidence and applies nothing. A ready result does not authorize remediation or prove repository correctness.

## Relationships and uncertainty

This is a mechanical alternative to `variant-001-readiness-invariant-model` and overlaps `$filesystem-git-observability`. Review should decide whether the evidence schema is general enough for adoption.

## Review questions

- Should restore-object reachability and byte identity be modeled separately?
- Should index-preservation capability be a typed method rather than a boolean?
