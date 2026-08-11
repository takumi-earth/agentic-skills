# Dataflow-aware-lint variant

## Concrete intent

Detect text-oracle laundering only when the compared value derives from parsed or transformed source.

## Approach

Bundle a conservative source-flow analyzer that tracks configured producers, propagators, wrappers, and sinks for substring, regex, prefix, suffix, raw equality, and snapshot operations while exempting declared exact-output owners.

## Preserved nuance

A repository-wide ban on string methods would be both brittle and overbroad. Findings are review signals unless a repository separately adopts the analyzer as a gate.

## Relationships and uncertainty

This mechanically complements `$test-adaptive-source-transforms`. Review should decide whether the lightweight flow model is useful before a compiler-integrated lint exists.
