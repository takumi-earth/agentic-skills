# Intent: variant-003-goal-response-artifacts

## Concrete use

Attach `managedObjectiveArtifacts` to the selected goal-tool response profile from the same committed goal snapshot and an attributable invocation input. Keep the metadata event-local.

## Preserved approach

Add managed artifacts only to GoalToolResponse to keep ThreadGoal stable.

Derive and attach managed artifact metadata at goal-tool response construction, pass it unchanged through PostToolUse, and document that it is event-local rather than durable goal state.

## Difference from sibling variants

Keep this approach distinct from `variant-001-post-tool-use-codex-home`, `variant-002-thread-goal-artifacts`. Do not converge implementation authority, activation effects, or failure semantics merely because common text could be shared.

## Causal evidence

The recorded failure preserved objective prose; the missing typed field was not its demonstrated cause. A response sidecar can carry a typed observation. It removes downstream prose parsing only if its producer receives an independent authoritative designation; event-local metadata alone cannot recover an association after resume.

- `user-designated authoritative source` at `~/rust-forks/codex-orig`: This checkout is the source for the running Codex binary.
- `direct source inspection` at `codex-source-findings.json`: ThreadGoal carries objective text but no managed artifact field; PostToolUse carries tool input and response but no typed codex_home.
- `inference` at `current review`: A typed contract is a future architectural improvement, not the present root cause.

## Validation planned

- create and update tool response
- PostToolUse pass-through
- resume without prior response
- compatibility with clients deserializing ThreadGoal

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
