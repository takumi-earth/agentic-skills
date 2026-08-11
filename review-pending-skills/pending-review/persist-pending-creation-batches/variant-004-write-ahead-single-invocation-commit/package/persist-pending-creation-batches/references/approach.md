# Approach contract

## Identity

- Candidate: `persist-pending-creation-batches`
- Variant: `variant-004-write-ahead-single-invocation-commit`
- Classification: convergence of `variant-001-single-invocation-commit` and `variant-002-write-ahead-batch-manifest`

## Required behavior

Persist every complete candidate root from one automatic-creation invocation in one Git commit. After validation and caller-owned staging, freeze the exact staged objects and precommit OID in an immutable manifest. Recheck that evidence before the caller commits, then prove one resulting commit contains the same complete trees and append its OID to a separate result record.

The staged-object snapshot contains each pathname, blob digest, Git mode, and symlink target. Working-tree bytes are not commit-content authority.

## Adopted predecessor behavior

- From `variant-001-single-invocation-commit`: one invocation-wide commit, exact complete candidate-root scope, unrelated-index rejection, candidate-remainder rejection, and a one-commit transition.
- From `variant-002-write-ahead-batch-manifest`: exclusive manifest creation, validation-evidence hashes, schema validation, postcommit verification, and an append-only result record.
- Convergence change: create and verify the content snapshot from the Git index after caller-owned staging, then compare the resulting commit tree with that same snapshot.

## Causal barriers

1. Complete creation before validation.
2. Complete validation before staging.
3. Complete caller-owned staging before manifest creation.
4. Verify the unchanged manifest, evidence, `HEAD`, index, and candidate remainder immediately before commit.
5. Create one caller-owned commit before later candidate edits.
6. Verify commit-tree parity and append the result before beginning later repairs.

Reordering permits stale validation, working-tree/index divergence, unrelated-path absorption, split commits, or later edits to become indistinguishable from the original creation checkpoint.

## Activation boundary

This nested package is pending. Its relationship to `$auto-skill-creator` records the intended owner and does not authorize an official merge, staging, committing, synchronization, or any hook or configuration change.
