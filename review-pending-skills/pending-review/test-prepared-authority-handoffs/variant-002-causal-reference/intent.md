# Causal-reference variant

## Concrete intent

Represent prepared-result handoffs as a narrow causal pattern routed through `$protect-causal-architecture` rather than a broad standalone workflow skill.

## Approach

Keep the main pending package compact and load one reference only when preparation changes field-level authority before a mutation barrier.

## Preserved nuance

The pattern does not ban all raw-input reads, require workflow tests for pure conversions, or create an audit artifact by default. It protects only the field and downstream edge whose owner changed.

## Relationships and uncertainty

This is an alternative to the standalone handoff contract and a possible future reference relationship for `$protect-causal-architecture`. Review should decide whether selective routing is sufficiently discoverable.

## Review questions

- Should the reference be merged into `$protect-causal-architecture` or remain a dedicated triggered skill?
- Does the minimal causal packet preserve enough test detail without the full matrix?
- Should fixture-role rules be linked to a separate promoted candidate?

