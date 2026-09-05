# Capability-gates variant

## Concrete intent

Explore a more formal alternative to the existing procedural owners for workflows where one artifact crosses repository, installer, harness, hook, and runtime boundaries.

## Approach

Represent every effect as a capability edge with its own mutator, authority, new discoverability or execution power, and positive/negative evidence. Execute only edges explicitly granted.

## Preserved nuance

This approach detects commands that bundle creation and activation, and it treats writes through existing live projections as activation. It does not assume the lifecycle has exactly four stages.

## Differences from the existing owners

Governing guidance and `$protect-causal-architecture` cover creation, enablement, and bundled commands without a mandatory matrix. This variant retains the more formal per-effect capability matrix for comparison in fragile workflows; its context cost remains an open review question.

## Review questions

- Is the matrix worth its context cost outside fragile multi-system workflows?
