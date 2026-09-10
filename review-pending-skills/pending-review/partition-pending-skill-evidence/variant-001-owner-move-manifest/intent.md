# Intent: variant-001-owner-move-manifest

## Concrete use

Keep run-specific evidence instances in scratch while placing reusable evidence schemas, scripts, instructions, and references inside explicitly owned pending variants.

## Preserved approach

Assign each reusable resource to one owning variant and move pre-existing scratch resources through a validated source-to-destination manifest.

Classify artifacts as evidence instances or reusable resources. Require the declared candidate and variant to exist completely, validate the selected source without following symlinks, publish verified bytes without replacing a destination, remove only the unchanged selected source, and report completed, partial, and remaining effects. Update task-required provenance without moving evidence instances.

## Difference from sibling variants

Keep this approach distinct from `variant-002-direct-owner-emission`, `variant-003-typed-model-schema`. Do not converge implementation authority, activation effects, or failure semantics merely because common text could be shared.

## Causal evidence

The enhancer scratch run was being treated as both investigation evidence storage and a multi-candidate product workspace. The user clarified that evidence instances and raw/memory/source context belong in scratch, while the reusable evidence JSON schema and product resources belong to pending-review owners.

- `live user correction` at `retained visible turn after creator instruction fix`: Potential-skill resources must be separated into appropriately named pending-review folders and moved after destinations exist.
- `newest live user correction` at `retained visible turn`: Investigation evidence and raw, memory, and source contexts stay in scratch; the evidence JSON schema does not.
- `pending-store source inspection` at `~/agentic-skills/review-pending-skills/scripts/pending_skill_inventory.py`: Every top-level pending directory must be a complete candidate and every child must be a complete variant; variant-local extra resources are permitted.

## Validation planned

- positive multi-resource move
- missing source
- existing destination
- escaping destination
- duplicate source owner
- hash mismatch
- evidence-instance exclusion

## Uncertainty and risk

- Moving evidence instances that must remain audit context.
- Creating an invalid shared top-level pending directory.
- Duplicating a shared schema into several candidates.
- Leaving stale provenance after a move.
- Treating a schema instance and its schema definition as the same artifact class.

The candidate remains pending because structural validity does not decide whether this design should be promoted or merged into an existing owner.

## Questions for review

- Does this approach preserve the narrowest semantic owner?
- Is its authority source available in every intended harness and deployment topology?
- Should shared behavior remain a relationship or later converge into an existing skill?
- Which activation effects, if any, should the user separately authorize?

## Possible activation effects

- none during pending creation
- future promotion could change automatic creator storage layout
