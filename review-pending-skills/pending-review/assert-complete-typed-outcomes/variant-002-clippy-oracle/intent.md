# Clippy-oracle variant

## Concrete intent

Provide a standalone Rust diagnostic workflow for warnings caused by a test-only call to a production projection.

## Approach

Trace real consumers and type semantics, choose complete equality or an existing domain projection, protect genuine public APIs, and separate source repair from lint verification.

## Preserved nuance

The skill does not assume every `single_call_fn` is a test problem, every public unused method is dead, or every complete type has appropriate equality semantics.

## Relationships and uncertainty

This variant overlaps `$rstriage` and `$implement-strict-work` but has a narrower automatic trigger. Review should decide whether one concrete warning justifies a standalone skill or should remain an implementation reference.

## Review questions

- Should the trigger include only `single_call_fn`, or analogous dead-code warnings caused by tests?
- Should the skill route strict repositories through `$guard-strict-work` explicitly?
- Is the public extension-seam distinction clear enough without a packaged reference?

