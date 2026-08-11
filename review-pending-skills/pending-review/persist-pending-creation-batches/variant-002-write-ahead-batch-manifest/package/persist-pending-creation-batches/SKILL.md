---
name: persist-pending-creation-batches
description: "Persist one automatic-creation invocation as one Git commit containing every complete candidate root, before any later edit begins. Use when an automatic skill-creation invocation produces one or more pending candidate roots and must persist the initial set before later review edits."
---

# Persist Pending Creation Batches

Apply the `variant-002-write-ahead-batch-manifest` design without silently merging it with sibling approaches.

## Preserve authority

- Treat this nested package as pending review until the user separately authorizes promotion and enablement.
- Preserve run-specific evidence in the canonical repository scratchpad and keep reusable product resources in this package.
- Do not register hooks, edit Codex source, change configuration, synchronize installations, stage unrelated work, or publish as an implied consequence of using this skill.
- Render paths beneath the user home as `~/...` and invoke environment-selected tools instead of hard-coded interpreter paths.

## Apply this design

Hash every candidate root plus its inventory and validation reports, persist the intended commit set and precommit OID in an immutable manifest, require staged names and current hashes to match, commit once, and append the resulting hash to a separate result record without editing candidate metadata or the manifest.

Use the helper lifecycle:

1. Run `create` after validation and before staging. It requires exact `review-pending-skills/pending-review/<candidate-name>` roots and creates, but never overwrites, the version-two manifest.
2. Stage the declared complete roots through the calling workflow.
3. Run `verify` to reject missing roots, unrelated staged paths, stale evidence, tree drift, and index or worktree remainder.
4. Commit once through the calling workflow.
5. Run `record-commit` to require a one-commit transition and append a version-one record to the selected JSONL result. The helper never stages or commits.

Use this sequence:

1. Identify the authority source and exact input facts before making a policy decision.
2. Apply only the contract documented in `references/approach.md` and its directly named resources.
3. Emit the checked condition, expected value, received value, and stable outcome whenever the design can fail.
4. Keep machine-readable output valid and separate from explanatory prose when a harness schema controls stdout.
5. Stop before any activation, synchronization, external mutation, or scope expansion not explicitly authorized by the user.

## Validate proportionately

- Prove manifest determinism.
- Prove post-manifest file drift.
- Prove extra or missing staged path.
- Prove malformed schema and stale validation evidence.
- Prove index and worktree divergence.
- Prove commit hash append after success.
- Prove a multi-commit transition fails.

Report assertions and process exit status separately. A nonzero command is diagnostic evidence, not a passing gate.

## Guard known risks

- Guard against Absorbing unrelated staged work.
- Guard against Splitting the invocation after validation to work around index conflicts.
- Guard against Committing a descendant rather than a full candidate root.
- Guard against Editing candidates again before the initial creation commit.
- Guard against Retaining a rejected per-candidate variant without clearly marking its provenance.

## Load resources

- Read `references/approach.md` before applying this variant's design.
- Read `references/creation-batch.schema.json` before producing or consuming a manifest.
- Read `references/creation-batch-result.schema.json` before consuming the append-only result.
- Run `scripts/verify_creation_batch.py` for the deterministic operation it owns; use its `--self-test` before relying on it.
