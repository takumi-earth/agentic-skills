# Intent: variant-001-post-tool-use-codex-home

## Concrete use

Supply a versioned `runtime_context.codex_home` from the session runtime. This resolves runtime location only; artifact identity and user designation remain separate.

## Preserved approach

Supply one versioned `runtime_context.codex_home` through a trusted `PostToolUse` input profile.

Use the runtime-context specification's exact field contract, trusted launch binding, and explicit legacy/new consumer profiles. It supplies a root, not an artifact selection.

## Difference from sibling variants

Keep this approach distinct from `variant-002-thread-goal-artifacts`, `variant-003-goal-response-artifacts`. Do not converge implementation authority, activation effects, or failure semantics merely because common text could be shared.

## Causal evidence

The recorded failure preserved objective prose; the missing typed field was not its demonstrated cause. A runtime root can remove root inference from package topology. It does not identify the objective artifact or eliminate selection from objective prose.

- `user-designated authoritative source` at `~/rust-forks/codex-orig`: This checkout is the source for the running Codex binary.
- `direct source inspection` at `codex-source-findings.json`: ThreadGoal carries objective text but no managed artifact field; PostToolUse carries tool input and response but no typed codex_home.
- `inference` at `current review`: A typed contract is a future architectural improvement, not the present root cause.

## Validation planned

- schema serialization fixture
- old handler compatibility
- custom CODEX_HOME
- resume and fork event parity

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
