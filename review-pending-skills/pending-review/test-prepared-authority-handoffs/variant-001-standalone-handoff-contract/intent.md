# Standalone handoff-contract variant

## Concrete intent

Protect field-level authority epochs created by schema, planning, normalization, or compilation engines and prove that downstream workflows consume the canonical prepared result.

## Approach

Build a raw-to-prepared-to-consumer matrix, remove stale rediscovery, preserve mutation and cleanup barriers, and require paired migrated-positive and genuinely-unresolved-negative workflow evidence.

## Preserved nuance

Prepared authority is field-specific. Raw input remains valid for unrelated facts, and the negative test must use a constructible production input rather than an artificial impossible prepared object.

## Relationships and uncertainty

This variant overlaps `$protect-causal-architecture`, `$plan-strict-work`, and `$audit-architectural-regressions`. Review should decide whether the handoff pattern recurs broadly enough for a standalone trigger or belongs as a causal reference.

## Review questions

- Should the workflow-level positive/negative pair be mandatory for every migrated field or only load-bearing authority?
- Should the skill explicitly require typestate when the owner API can encode the ordering?
- How much repository-specific vocabulary should remain in a promoted reference?

