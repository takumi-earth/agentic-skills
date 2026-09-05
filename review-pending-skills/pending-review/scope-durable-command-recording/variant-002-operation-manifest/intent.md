# Intent: variant-002-operation-manifest

## Concrete use

Require durable scripts and persisted reports for substantive computation, mutation, and evidence production without wrapping passive instruction or source reads in unnecessary task scripts.

## Preserved approach

Require every substantive operation to be declared in a durable argv manifest consumed by one generic runner.

Persist cwd, inputs, exact argv, expected conditions, outputs, and timeout before execution; keep passive reads outside the manifest; refuse shell interpolation and unlisted side effects.

## Difference from sibling variants

The user approved pruning `variant-001-effect-classification` after clarifying the evidence boundary in `$filesystem-git-observability`, and pruning the rejected `variant-003-record-every-command` comparison. Their names and the predecessor path in `review.json` are Git-history references. This manifest-driven approach remains a distinct pending design.

## Current review disposition

Retain pending. `filesystem-git-observability/scripts/persist_command_report.py` already preserves exact argv, input hashes, stdout, stderr, and exit status. This candidate provides a manifest schema and proposed runner contract; it has no runner implementation. Reconcile its proposed `cwd`, timeout, expected-condition, and output enforcement with that helper and the existing owner's task-required evidence boundary before implementing a runner or proposing promotion.

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
