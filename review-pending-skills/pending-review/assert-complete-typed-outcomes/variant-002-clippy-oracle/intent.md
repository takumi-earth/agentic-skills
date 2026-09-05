# Clippy-oracle variant

## Concrete intent

Provide a standalone Rust diagnostic workflow for warnings caused by a test-only call to a production projection.

## Approach

Trace real consumers and type semantics, choose complete equality or an existing domain projection, protect genuine public APIs, and separate source repair from lint verification.

## Preserved nuance

The skill does not assume every `single_call_fn` is a test problem, every public unused method is dead, or every complete type has appropriate equality semantics.

## Relationships and uncertainty

Retain this variant pending as a distinct general Rust automatic diagnostic alternative. Its trigger includes test-created `single_call_fn`, `dead_code`, and analogous warnings beyond the strict ecosystem. Folding the shared assertion pattern into `$implement-strict-work` does not adopt or replace that broader trigger. `$rstriage` has a different invocation and mutation contract and is not an equivalent owner without further review.

The approved `variant-001-implement-strict-pattern` was folded into `implement-strict-work/references/typed-outcome-assertions.md` and pruned. Its alternative relationship is historical; the optional owner reference preserves the shared equality, consumer, and helper guidance.

## Review requirements before adoption

- Resolve public API authority explicitly before introducing a new comparison contract; the preference order is not permission to add one.
- Route strict work through `$guard-strict-work`, `$implement-strict-work`, and `$verify-strict-work` with their API, exception, and execution boundaries intact.
- Preserve the distinction between a supported public extension seam and test convenience without inferring deletion authority from local reachability. Keep the standalone trigger and invocation contract pending user selection.
