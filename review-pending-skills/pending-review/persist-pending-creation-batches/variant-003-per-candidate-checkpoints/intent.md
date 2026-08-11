# Intent: variant-003-per-candidate-checkpoints

## Concrete comparison use

Retain the rejected per-candidate checkpoint strategy as comparison evidence for reviews of commit fragmentation and recovery granularity. Never route an active creation batch through this variant.

## Preserved approach

The rejected strategy would persist each complete candidate root separately as soon as it validates.

Retain the superseded per-candidate checkpoint design for comparison, explicitly record the user's rejection and the fragmentation cost, and never execute it during the controlling grouped-commit workflow.

## Difference from sibling variants

Keep this approach distinct from `variant-001-single-invocation-commit`, `variant-002-write-ahead-batch-manifest`. Do not converge implementation authority, activation effects, or failure semantics merely because common text could be shared.

## Causal evidence

The prior creator contract treated each candidate root as a separate commit lane. The user clarified that candidate roots are indivisible path units inside one invocation batch, not a mandate to create many commits; the initial commit is the boundary before later edits.

- `live user correction` at `retained visible turn`: Create all candidates and commit them in that go; do not create roughly twenty commits.
- `live user correction` at `retained visible turn`: The commit requirement means persist the initial creation before editing the candidates again.
- `authorized canonical maintenance` at `~/agentic-skills/auto-skill-creator/SKILL.md`: The current worktree now specifies one invocation-batch commit while preserving complete candidate roots as path units.

## Validation planned

- demonstrate commit-count growth
- compare recovery granularity
- confirm variant remains pending and inactive

## Uncertainty and risk

- Absorbing unrelated staged work.
- Splitting the invocation after validation to work around index conflicts.
- Committing a descendant rather than a full candidate root.
- Editing candidates again before the initial creation commit.
- Retaining a rejected per-candidate variant without clearly marking its provenance.

The candidate remains pending because structural validity does not decide whether this design should be promoted or merged into an existing owner.

## Questions for review

- Does this approach preserve the narrowest semantic owner?
- Is its authority source available in every intended harness and deployment topology?
- Should shared behavior remain a relationship or later converge into an existing skill?
- Which activation effects, if any, should the user separately authorize?

## Possible activation effects

- none during pending creation
- comparison-only review; no operational promotion or activation is recommended
