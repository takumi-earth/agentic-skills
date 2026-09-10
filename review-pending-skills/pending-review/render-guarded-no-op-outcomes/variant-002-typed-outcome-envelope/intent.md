# Typed outcome-envelope variant

## Concrete intent

Make guarded mutation results machine-checkable and render the same semantics consistently for users.

## Approach

Validate a typed JSON envelope for `write`, `no-op`, `blocked`, `failed`, or `verified`, enforce outcome-specific invariants, and produce a deterministic human explanation.

## Preserved nuance

Verification is a distinct fact even when represented as an outcome. A no-op requires positive desired-state proof, not merely a zero write count.

## Relationships and uncertainty

This remains a mechanical alternative to `variant-001-no-op-reporting-vocabulary`, whose reporting rule the user approved folding into `$design-command-observability` before pruning the draft. The predecessor and alternative names in `review.json` are Git-history references. The executable still overlaps `$filesystem-git-observability` and `$design-command-observability`.

## Current review disposition

Retain the corrected envelope as an adoption alternative. The approved correction contract is applied:

- Align schema and CLI validation, including required fields, additional properties, nonempty conditions, and outcome-specific invariants.
- Reject malformed outcome and verification types with the intended diagnostic and exit status instead of an uncaught exception.
- Preserve actual effects and write counts in failure and verification summaries, include the facts needed to explain the desired state, and normalize home paths in rendered output and diagnostics.
- Resolve the existing question about `verified` as an outcome so verification cannot obscure the underlying application result.

The schema and executable now enforce these requirements. A `verified` envelope names its underlying `application_outcome`, so it cannot hide a blocked or failed application or its completed writes.

## Review questions

- Verification remains orthogonal in its existing field; the retained `verified` presentation tag requires the underlying application outcome explicitly.
- Which error and value fields need typed redaction before human rendering?
