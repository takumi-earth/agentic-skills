# Opaque-typed-harness variant

## Concrete intent

Make typed structural assertions the easiest available test interface while withholding rendered-source escape hatches.

## Approach

Define an opaque workspace result that exposes owners, typed candidates, selected nodes, semantic deltas, changed paths, outcomes, and replay while omitting raw text, serialization, debug rendering, `Display`, `Deref<str>`, `AsRef<str>`, and unrestricted parser-node access.

## Preserved nuance

Exact text remains valid when text or bytes are the documented product contract, but that suite must use a separate result type and owner.

## Relationships and uncertainty

This overlaps `$test-adaptive-source-transforms` and `$verify-test-parity`. Review should decide whether the API contract should remain language-neutral or gain Rust compile-fail examples.
