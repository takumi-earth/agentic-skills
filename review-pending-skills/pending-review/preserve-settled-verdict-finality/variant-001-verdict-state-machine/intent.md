# Verdict state-machine variant

## Concrete intent

Stop settled or applied decision units from returning to reassessment or renewed countersignature merely because context, HEAD, the index, or plan prose changed.

## Approach

Track each unit through explicit states and require a direct, attributable user supersession before any transition from `settled` or `applied` back to an unresolved state.

## Preserved nuance

New facts may invalidate an application guard without reopening the underlying verdict. Historical blocked or pending wording may remain when clearly attributed as history.

## Relationships and uncertainty

This overlaps `$guard-strict-work`, `$maintain-living-goal`, and `$reconcile-live-steering`. Review should decide whether finality belongs in one of those owners or warrants a narrow standalone trigger.

## Review questions

- What exact user language is sufficient to supersede a settled unit?
- Should guard invalidation and verdict reopening be modeled as wholly separate axes?
