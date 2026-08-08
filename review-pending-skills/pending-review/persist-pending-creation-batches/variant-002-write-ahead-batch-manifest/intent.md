# Intent: variant-002-write-ahead-batch-manifest

## Concrete use

Persist one automatic-creation invocation as one Git commit containing every complete candidate root, before any later edit begins.

## Preserved approach

Freeze the complete root set and validation state in a write-ahead manifest before staging the one batch commit.

Hash every candidate root, persist the intended commit set, require staged names and current hashes to match the manifest, commit once, and append the resulting hash without editing candidate metadata.

## Difference from sibling variants

Keep this approach distinct from `variant-001-single-invocation-commit`, `variant-003-per-candidate-checkpoints`. Do not converge implementation authority, activation effects, or failure semantics merely because common text could be shared.

## Causal evidence

The prior creator contract treated each candidate root as a separate commit lane. The user clarified that candidate roots are indivisible path units inside one invocation batch, not a mandate to create many commits; the initial commit is the boundary before later edits.

- `live user correction` at `retained visible turn`: Create all candidates and commit them in that go; do not create roughly twenty commits.
- `live user correction` at `retained visible turn`: The commit requirement means persist the initial creation before editing the candidates again.
- `authorized canonical maintenance` at `~/agentic-skills/auto-skill-creator/SKILL.md`: The current worktree now specifies one invocation-batch commit while preserving complete candidate roots as path units.

## Validation planned

- manifest determinism
- post-manifest file drift
- extra or missing staged path
- commit hash append after success

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
- future promotion could change auto-skill-creator Git persistence semantics
