# Prepared Authority Handoffs

Load this reference only when preparation creates a new authority epoch for a field.

## Minimal causal packet

- Before owner: raw document, request, legacy model, or unnormalized IR.
- Allowed transition: parser, schema engine, normalizer, planner, or compiler validates and prepares canonical state.
- After owner: exact prepared accessor or typed field.
- First consumer: exact orchestration decision.
- Barrier: last prewrite/pre-effect point.
- First mutator: exact write, process, repository, or external effect.
- Counterfactual: stale rediscovery rejects or misattributes a value already resolved by preparation.
- Positive evidence: constructible raw input that becomes valid prepared authority and completes the workflow.
- Negative evidence: constructible raw input with no authority source that fails before mutation.

## Decision rule

For each later raw read, ask whether preparation interprets that exact field:

- If yes, consume the prepared field.
- If no, retain the raw fact if it remains independently owned.
- If ownership is ambiguous, stop only the dependent effect and resolve the field-level owner.

## Barrier rule

Changing the authority read must not move preflight, mutation, recovery, cleanup, or persistence. Test both the value handoff and the causal boundary.

