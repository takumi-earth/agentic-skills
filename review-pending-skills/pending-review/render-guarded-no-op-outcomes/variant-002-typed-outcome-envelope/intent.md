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

Retain pending correction. The envelope and renderer have not been adopted into an official owner. Before adoption:

- Align schema and CLI validation, including required fields, additional properties, nonempty conditions, and outcome-specific invariants.
- Reject malformed outcome and verification types with the intended diagnostic and exit status instead of an uncaught exception.
- Preserve actual effects and write counts in failure and verification summaries, include the facts needed to explain the desired state, and normalize home paths in rendered output and diagnostics.
- Resolve the existing question about `verified` as an outcome so verification cannot obscure the underlying application result.

These requirements record the review findings; the executable and its schema remain unchanged pending correction.

## Review questions

- Should verification be an orthogonal phase field instead of an outcome value?
- Which error and value fields need typed redaction before human rendering?
