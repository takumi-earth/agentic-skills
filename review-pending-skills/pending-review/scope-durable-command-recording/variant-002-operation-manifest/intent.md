# Intent: variant-002-operation-manifest

## Concrete use

Require durable scripts and persisted reports for substantive computation, mutation, and evidence production without wrapping passive instruction or source reads in unnecessary task scripts.

## Preserved approach

Require every substantive operation to be declared in a durable argv manifest consumed by one generic runner.

Persist cwd, inputs, exact argv, expected conditions, outputs, and timeout before execution; keep passive reads outside the manifest; refuse shell interpolation and unlisted side effects.

## Difference from sibling variants

Keep this approach distinct from `variant-001-effect-classification`, `variant-003-record-every-command`. Do not converge implementation authority, activation effects, or failure semantics merely because common text could be shared.

## Causal evidence

The durable-script mandate was correctly intended to make investigation and mutation repeatable, but it was over-applied to a passive SKILL.md read. That added indirection and caused an avoidable unsupported-flag failure without improving auditability.

- `controlling user instruction` at `retained conversation`: Write substantive scripts to files for repeatability and auditability; ad hoc shell procedures are not permitted.
- `live user correction` at `retained visible turn`: Do not use a script merely to read a skill.
- `durable failure evidence` at `review-ledger event 005-direct-skill-reads`: The wrapper expected a positional path but received an unsupported --path flag; the corrected boundary reserves scripts for substantive effects.

## Validation planned

- exact argv preservation
- home-path normalization
- undeclared output rejection
- passive read exemption
- nonzero diagnostic reporting

## Uncertainty and risk

- Calling a substantive source selection a passive read to evade durability.
- Wrapping trivial reads and obscuring intent.
- Treating a persisted report as proof that a flawed procedure is correct.
- Retaining the rejected record-every-command variant without marking it inactive.

The candidate remains pending because structural validity does not decide whether this design should be promoted or merged into an existing owner.

## Questions for review

- Does this approach preserve the narrowest semantic owner?
- Is its authority source available in every intended harness and deployment topology?
- Should shared behavior remain a relationship or later converge into an existing skill?
- Which activation effects, if any, should the user separately authorize?

## Possible activation effects

- none during pending creation
- future promotion could change command-recording guidance across projects
