# Typed outcome-envelope variant

## Concrete intent

Make guarded mutation results machine-checkable and render the same semantics consistently for users.

## Approach

Validate a typed JSON envelope for `write`, `no-op`, `blocked`, `failed`, or `verified`, enforce outcome-specific invariants, and produce a deterministic human explanation.

## Preserved nuance

Verification is a distinct fact even when represented as an outcome. A no-op requires positive desired-state proof, not merely a zero write count.

## Relationships and uncertainty

This is a mechanical alternative to `variant-001-no-op-reporting-vocabulary` and overlaps `$filesystem-git-observability` and `$design-command-observability`.

## Review questions

- Should verification be an orthogonal phase field instead of an outcome value?
- Which error and value fields need typed redaction before human rendering?
