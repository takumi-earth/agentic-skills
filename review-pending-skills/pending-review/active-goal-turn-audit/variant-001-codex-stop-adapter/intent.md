# Codex Stop-adapter variant

## Concrete intent

Persist the current Codex-specific turn-ending hook design as a standalone skill candidate even though its implemented script currently lives under `$maintain-living-goal`.

## Approach

Own the adapter's lifecycle schema, read-only active-goal lookup, recursion boundary, audit prompt, and positive/negative validation as one narrowly triggered skill.

## Preserved nuance

The same-turn retry is not another harness goal turn, the three-turn blocker audit must not be manufactured, and turn-ending continuation cannot guard an earlier completion tool call. Creation and registration remain separate.

## Relationships and uncertainty

This candidate is deliberately repository- and harness-specific and overlaps `$maintain-living-goal`, `$design-command-observability`, and the newly created adapter resource. Review should decide whether standalone triggering improves reliability or merely splits one owner.

## Review questions

- Should the adapter remain a resource of `$maintain-living-goal` while this candidate becomes a testing/reference skill?
- Would a cross-harness variant preserve useful common semantics without erasing Codex's exact `Stop` schema?
