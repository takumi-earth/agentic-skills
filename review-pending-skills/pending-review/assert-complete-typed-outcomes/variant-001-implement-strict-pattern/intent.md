# Implement-strict pattern variant

## Concrete intent

Prevent strict Rust tests from manufacturing production API usage solely for convenient assertions and replace those projections with equal-or-stronger typed behavior evidence.

## Approach

Inspect complete outcome semantics and real consumers, prefer whole typed equality when meaningful, use existing domain projections when not, and extract shared expected-value helpers only when they express repeated domain vocabulary.

## Preserved nuance

Full equality is not automatically stronger when it pins nondeterministic or unrelated fields. Genuine downstream accessors remain supported, and unrun lint commands remain unverified.

## Relationships and uncertainty

This variant is a possible compact relationship for `$implement-strict-work` and overlaps `$rstriage`. Review should decide whether the concrete pattern belongs in general implementation guidance or warrants a standalone diagnostic trigger.

## Review questions

- Should a promoted form mention `single_call_fn` explicitly or stay lint-neutral?
- How should external public consumers be evidenced when they are outside the current workspace?
- Should the expected-value helper rule be shared with strict-test-support guidance?

