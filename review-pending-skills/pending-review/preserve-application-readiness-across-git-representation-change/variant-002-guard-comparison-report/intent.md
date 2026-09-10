# Guard comparison-report variant

## Concrete intent

Compare two guarded-application evidence snapshots and report whether only Git representation changed or a real application invariant drifted.

## Approach

Use a deterministic, read-only JSON comparator for content guards, restore objects, effect paths, index-preservation capability, HEAD, and index identity. Keep representation changes in a separate result field.

## Preserved nuance

The comparator consumes supplied evidence and applies nothing. A ready result does not authorize remediation or prove repository correctness.

## Relationships and uncertainty

This remains a mechanical alternative to `variant-001-readiness-invariant-model`, whose guidance the user approved folding into `filesystem-git-observability/references/guarded-application-readiness.md` before pruning the draft. The predecessor and alternative names in `review.json` are Git-history references.

## Current review disposition

Retain the corrected comparator as an adoption alternative. The approved correction contract is applied:

- Validate nested guard and restore records, complete effect-path coverage, and actual replacement availability; unchanged invalid inputs must not produce a ready result.
- Clarify deletion-only operations, operation identity beyond path names, and recovery methods that explicitly require an exact `HEAD` or index identity.
- Preserve the distinction between supplied evidence comparison and independently established application readiness, and normalize home paths in diagnostics.

The executable validates these supplied claims and keeps independent repository verification and application authority explicitly unestablished.

## Review questions

- Should restore-object reachability and byte identity be modeled separately?
- Should index-preservation capability be a typed method rather than a boolean?
