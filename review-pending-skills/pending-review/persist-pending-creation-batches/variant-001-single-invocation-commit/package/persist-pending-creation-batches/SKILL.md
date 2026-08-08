---
name: persist-pending-creation-batches
description: "Persist one automatic-creation invocation as one Git commit containing every complete candidate root, before any later edit begins. Use when an automatic skill-creation invocation produces one or more pending candidate roots and must persist the initial set before later review edits."
---

# Persist Pending Creation Batches

Apply the `variant-001-single-invocation-commit` design without silently merging it with sibling approaches.

## Preserve authority

- Treat this nested package as pending review until the user separately authorizes promotion and enablement.
- Preserve run-specific evidence in the canonical repository scratchpad and keep reusable product resources in this package.
- Do not register hooks, edit Codex source, change configuration, synchronize installations, stage unrelated work, or publish as an implied consequence of using this skill.
- Render paths beneath the user home as `~/...` and invoke environment-selected tools instead of hard-coded interpreter paths.

## Apply this design

Validate all variants first, reject unrelated staged paths, stage the full root set in one path-bounded command, require no candidate-root remainder, commit once, and prohibit later edits until the initial batch commit exists.

Use this sequence:

1. Identify the authority source and exact input facts before making a policy decision.
2. Apply only the contract documented in `references/approach.md` and its directly named resources.
3. Emit the checked condition, expected value, received value, and stable outcome whenever the design can fail.
4. Keep machine-readable output valid and separate from explanatory prose when a harness schema controls stdout.
5. Stop before any activation, synchronization, external mutation, or scope expansion not explicitly authorized by the user.

## Validate proportionately

- Prove multiple complete candidate roots.
- Prove unrelated staged path.
- Prove missing declared root.
- Prove unstaged candidate remainder.
- Prove single resulting commit.

Report assertions and process exit status separately. A nonzero command is diagnostic evidence, not a passing gate.

## Guard known risks

- Guard against Absorbing unrelated staged work.
- Guard against Splitting the invocation after validation to work around index conflicts.
- Guard against Committing a descendant rather than a full candidate root.
- Guard against Editing candidates again before the initial creation commit.
- Guard against Retaining a rejected per-candidate variant without clearly marking its provenance.

## Load resources

- Read `references/approach.md` before applying this variant's design.
- Read `references/batch-commit-contract.md` when its named contract is load-bearing.
- Run `scripts/verify_creation_batch.py` for the deterministic operation it owns; use its `--self-test` before relying on it.
