---
name: persist-pending-creation-batches
description: "Persist one automatic skill-creation invocation as one Git commit containing every complete pending candidate root, backed by immutable staged-object evidence. Use when an automatic creation batch has been validated and must be checkpointed before later candidate edits; do not use for ordinary candidate review, manual unrelated commits, or per-candidate checkpointing."
---

# Persist Pending Creation Batches

Apply the pending `variant-004-write-ahead-single-invocation-commit` convergence design. Treat the package as review evidence until the user separately authorizes a merge into `$auto-skill-creator`.

## Preserve the causal boundary

Use one commit for all complete candidate roots created or changed by one automatic-creation invocation. Keep each candidate root indivisible inside that batch.

1. Produce the deterministic inventory and validation reports for every variant.
2. Let the calling workflow stage only the exact complete candidate roots.
3. Run `create` to reject unrelated staged paths and candidate remainder, then exclusively write an immutable manifest of the staged Git objects and current `HEAD`.
4. Run `verify-precommit` immediately before the commit. Require the same staged pathnames, blob bytes, executable modes, symlink targets, evidence hashes, and precommit OID.
5. Let the calling workflow create exactly one commit. The helper must never stage or commit.
6. Run `record-postcommit` before any later candidate edit. Require one commit, the complete root set, and commit-tree parity with the manifest; append the precommit and resulting commit OIDs to a separate JSONL result.

Stop this commit lane when the index contains an unrelated path or any declared candidate has untracked or unstaged remainder. Preserve unrelated staged work and ask the caller to resolve the collision; do not unstage or absorb it.

## Keep evidence exact

- Require every root to equal `review-pending-skills/pending-review/<candidate-name>`.
- Read candidate contents from staged blobs and modes, never from working-tree bytes, when creating or verifying the commit snapshot.
- Treat mode `100755` as executable, mode `100644` as non-executable, and mode `120000` as a symlink whose target is the blob payload.
- Hash the inventory and every validation report and reject later drift.
- Create the manifest with exclusive no-overwrite semantics and write results append-only.
- Render paths beneath the user home as `~/...` in machine-readable output.

## Preserve authority

- Keep validation, staging, commit creation, and postcommit recording as distinct barriers.
- Do not stage, commit, register hooks, change configuration, synchronize installations, or publish from the helper.
- Do not promote or merge this nested package merely because its validation passes.
- Retain both predecessor variants as design evidence.

## Load and validate resources

- Read `references/approach.md` before applying the convergence design.
- Read `references/staged-object-contract.md` before creating or verifying a manifest.
- Read `references/creation-batch.schema.json` and `references/creation-batch-result.schema.json` when consuming persisted records.
- Run `python3 scripts/manage_creation_batch.py --self-test` and report assertion text separately from process exit status.
