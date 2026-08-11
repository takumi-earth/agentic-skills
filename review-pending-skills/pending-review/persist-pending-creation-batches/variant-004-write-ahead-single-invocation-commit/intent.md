# Intent: variant-004-write-ahead-single-invocation-commit

## Concrete use

Persist every complete candidate root produced by one automatic-creation invocation in one Git commit, with immutable evidence of the exact staged objects that the commit is expected to contain.

## Converged approach

Combine `variant-001-single-invocation-commit`'s one-invocation commit boundary with `variant-002-write-ahead-batch-manifest`'s immutable manifest and append-only result lifecycle.

Validate every nested package, stage every complete candidate root through the calling workflow, and then create one exclusive precommit manifest from the index. Record each staged pathname, blob digest, Git mode, and symlink target; reject unrelated staged paths and all untracked or unstaged candidate remainder. Recheck the same index snapshot immediately before the caller commits once, then prove that the resulting commit tree matches the manifest and append the precommit and resulting commit OIDs to a separate result record.

The helper inspects and persists evidence. It never stages or commits.

## Difference from predecessor variants

- Adopt the single invocation-wide commit and exact candidate-root boundary from `variant-001-single-invocation-commit`.
- Adopt the immutable write-ahead manifest, evidence hashing, and separate append-only result from `variant-002-write-ahead-batch-manifest`.
- Replace working-tree tree hashes with a manifest of staged Git objects so the evidence names the bytes and modes actually selected for commit.
- Create the manifest after validation and staging, rather than hashing candidate working-tree bytes before staging.
- Retain every predecessor unchanged as design evidence.

## Causal evidence

The prior creator contract treated each candidate root as a separate commit lane. The user clarified that candidate roots are indivisible path units inside one invocation batch, not a mandate to create many commits; the initial commit is the boundary before later edits.

- `live user correction` at `retained visible turn`: Create all candidates and commit them in that go; do not create roughly twenty commits.
- `live user correction` at `retained visible turn`: The commit requirement means persist the initial creation before editing the candidates again.
- `approved pending-skill review plan` at `active living goal`: Converge variants `001` and `002`, verify staged Git objects, and keep staging and committing with the calling workflow.

## Validation planned

- exact and malformed candidate roots
- multiple complete roots in one index snapshot
- unrelated staged paths and missing staged coverage
- untracked and unstaged candidate remainder
- staged blob-byte drift
- executable-mode drift
- symlink-target drift
- inventory and validation-report drift
- immutable manifest creation and schema validation
- one-commit transition and commit-tree parity
- rejection of multi-commit transitions
- append-only result records and duplicate-result rejection

## Uncertainty and risk

- Absorbing unrelated staged work.
- Treating working-tree bytes as proof of index contents.
- Splitting the invocation after manifest creation.
- Committing a descendant rather than the complete candidate root.
- Hiding staging or commit mutations inside the evidence helper.

The candidate remains pending because structural and behavioral validity do not independently authorize its merge into `$auto-skill-creator`.

## Possible activation effects

- none during pending creation
- future merge changes `$auto-skill-creator` creation-batch persistence semantics
