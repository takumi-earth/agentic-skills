# Intent: variant-002-operation-manifest

## Concrete use

Specify a durable command manifest when the authorized task requires recoverable evidence, preserving direct reads and focused checks.

## Preserved approach

Declare task-required operations through an adapter over the existing recorder rather than a competing runner.

Declare `cwd`, inputs, exact `argv`, expected conditions, operation outputs, report path, purpose, and timeout. Preserve exact arguments without shell interpolation; distinguish declared scope from implemented enforcement.

## Difference from sibling variants

The user approved pruning `variant-001-effect-classification` after clarifying the evidence boundary in `$filesystem-git-observability`, and pruning the rejected `variant-003-record-every-command` comparison. Their names and the predecessor path in `review.json` are Git-history references. This manifest-driven approach remains a distinct pending design.

## Current review disposition

The approved reconciliation is applied in `references/runner-contract.md`: each manifest field maps to the current recorder or explicitly identifies a missing capability. The schema and specification remain pending adoption; this package has no executable adapter. Implementing that proposed capability is separate from completing the approved specification correction.

## Causal evidence

The durable-script mandate was correctly intended to make investigation and mutation repeatable, but it was over-applied to a passive SKILL.md read. That added indirection and caused an avoidable unsupported-flag failure without improving auditability.

- `controlling user instruction` at `retained conversation`: Write substantive scripts to files for repeatability and auditability; ad hoc shell procedures are not permitted.
- `live user correction` at `retained visible turn`: Do not use a script merely to read a skill.
- `durable failure evidence` at `review-ledger event 005-direct-skill-reads`: The wrapper expected a positional path but received an unsupported --path flag; the corrected boundary reserves scripts for substantive effects.

## Validation planned

- exact argv preservation
- home-path normalization
- declared versus enforced output scope
- passive read exemption
- nonzero diagnostic reporting

## Uncertainty and risk

- Treating a manifest declaration as enforcement of a command's effects.
- Wrapping trivial reads and obscuring intent.
- Treating a persisted report as proof that a flawed procedure is correct.
- Treating a label such as substantive computation as authority to create evidence artifacts.

The candidate remains pending because structural validity does not decide whether this design should be promoted or merged into an existing owner.

## Questions for review

- Does this approach preserve the narrowest semantic owner?
- Is its authority source available in every intended harness and deployment topology?
- Should shared behavior remain a relationship or later converge into an existing skill?
- Which activation effects, if any, should the user separately authorize?

## Possible activation effects

- none during pending creation
- future promotion could change command-recording guidance across projects
