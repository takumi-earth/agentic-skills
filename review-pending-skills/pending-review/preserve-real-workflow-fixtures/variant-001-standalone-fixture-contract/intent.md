# Standalone fixture-contract variant

## Concrete intent

Require workflow and integration tests to preserve the real on-disk role, provenance, and toolchain treatment of every scenario-defining artifact.

## Approach

Classify inputs by production role, require committed exact-byte fixtures when file identity or tooling matters, distinguish valid source from inert invalid snippets, and separate semantic oracles from input construction. Permit inline values only for genuine value-level APIs.

## Preserved nuance

Role-specific files remain distinct even when byte-identical. The contract does not demand fixture files for every parser string, broaden one touched scenario into repository-wide migration, or eliminate compile-fail files when full compiler integration is the behavior under test.

## Relationships and uncertainty

This variant overlaps `$plan-strict-work`, `$implement-strict-work`, and `$protect-causal-architecture`. Review should decide whether fixture ownership needs an independently triggered skill or should become shared guidance routed through those owners.

## Review questions

- Should exact-byte loading be required for every workflow fixture or only scenario-defining inputs?
- Should the valid-source rule remain language-neutral in the main skill and keep Rust examples in the reference?
- Should promotion retain a separate reference or fold the compact role matrix into an existing strict testing contract?

