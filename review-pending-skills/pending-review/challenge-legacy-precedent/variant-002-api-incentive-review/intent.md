# API-incentive-review variant

## Concrete intent

Review whether a helper API makes a prohibited shortcut easier than the required semantic behavior.

## Approach

Inspect inputs, outputs, default selectors, failure states, and assertion surfaces for raw rendered strings, global counts, fixed paths, complete bodies, boolean applicability, first-match mutation, and missing ambiguity or replay representation.

## Preserved nuance

Strings, booleans, paths, and exact output are not intrinsically wrong. The issue is whether the API assigns them correctness authority under a stronger semantic invariant.

## Relationships and uncertainty

This is a helper-surface alternative to the counterfactual packet and overlaps `$protect-causal-architecture`. Review should decide whether it is too narrow for standalone triggering.
