# Intent: variant-002-thread-goal-artifacts

## Concrete use

Persist a versioned `managedObjectiveArtifacts` association with the exact goal and objective revision. Preserve it across status changes; explicitly replace or clear it when the objective changes.

## Preserved approach

Persist managed objective artifacts on ThreadGoal state and protocol events.

Persist the exact goal/revision association across status-only changes and explicitly replace or clear it when objective text changes. Expose it through the selected protocol without rewriting human objective text.

## Difference from sibling variants

Keep this approach distinct from `variant-001-post-tool-use-codex-home`, `variant-003-goal-response-artifacts`. Do not converge implementation authority, activation effects, or failure semantics merely because common text could be shared.

## Causal evidence

The recorded failure preserved objective prose; the missing typed field was not its demonstrated cause. An attributable durable association can remove future consumers' prose-based selection. The trusted designation input and lossless lifecycle migration must actually be implemented before that behavior can be claimed.

- `user-designated authoritative source` at `~/rust-forks/codex-orig`: This checkout is the source for the running Codex binary.
- `direct source inspection` at `codex-source-findings.json`: ThreadGoal carries objective text but no managed artifact field; PostToolUse carries tool input and response but no typed codex_home.
- `inference` at `current review`: A typed contract is a future architectural improvement, not the present root cause.

## Validation planned

- goal create/update response
- resume persistence
- legacy serialized state
- multiple artifact kinds
- deleted artifact behavior

## Uncertainty and risk

- Protocol migration and version skew.
- Persisting host-specific paths across machines.
- Ambiguous ownership between goal state and hook event context.
- Expanding scope beyond the confirmed hook bug.

The approved specification corrections are complete. The candidate remains pending adoption as a distinct inert design; runtime implementation and enablement are separate effects. Concrete types, outcomes, compatibility rules, and attributed source seams are in the packaged references.

## Questions for review

- Does this approach preserve the narrowest semantic owner?
- Is its authority source available in every intended harness and deployment topology?
- Should shared behavior remain a relationship or later converge into an existing skill?
- Which activation effects, if any, should the user separately authorize?

## Possible activation effects

- none during pending creation
- future use could guide a breaking or additive Codex protocol change
