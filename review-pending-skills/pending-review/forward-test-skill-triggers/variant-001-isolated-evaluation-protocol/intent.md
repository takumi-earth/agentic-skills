# Isolated-evaluation-protocol variant

## Concrete intent

Test whether a skill activates and executes correctly without inherited conversation history supplying its conclusions.

## Approach

Define isolated explicit, implicit, nearest-negative, mixed-owner, and unauthorized-effect evaluations using raw prompts and artifacts, then score activation separately from contract execution.

## Preserved nuance

Designing an evaluation does not authorize delegation. Full-history review remains valid for the question it answered but cannot prove fresh trigger reachability.

## Relationships and uncertainty

This overlaps `$audit-skill-trigger-contracts` and system `$skill-creator`. Review should decide whether evaluation result storage belongs here or in an external harness owner.
