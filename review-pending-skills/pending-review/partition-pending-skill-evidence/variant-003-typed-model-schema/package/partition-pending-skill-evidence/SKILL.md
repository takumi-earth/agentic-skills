---
name: partition-pending-skill-evidence
description: "Keep run-specific evidence instances in scratch while placing reusable evidence schemas, scripts, instructions, and references inside explicitly owned pending variants. Use when automatic skill workflows create evidence records, schemas, or reusable resources across scratch and pending-review storage."
---

# Partition Pending Skill Evidence

Apply the `variant-003-typed-model-schema` design without silently merging it with sibling approaches.

## Preserve authority

- Treat this nested package as pending review until the user separately authorizes promotion and enablement.
- Preserve run-specific evidence in the canonical repository scratchpad and keep reusable product resources in this package.
- Do not register hooks, edit Codex source, change configuration, synchronize installations, stage unrelated work, or publish as an implied consequence of using this skill.
- Render paths beneath the user home as `~/...` and invoke environment-selected tools instead of hard-coded interpreter paths.

## Apply this design

Keep one typed source model, generate deterministic JSON Schema as a product resource, validate scratch evidence instances against it without relocating them, and fail when generated schema drifts from the typed model.

Use this sequence:

1. Identify the authority source and exact input facts before making a policy decision.
2. Apply only the contract documented in `references/approach.md` and its directly named resources.
3. Emit the checked condition, expected value, received value, and stable outcome whenever the design can fail.
4. Keep machine-readable output valid and separate from explanatory prose when a harness schema controls stdout.
5. Stop before any activation, synchronization, external mutation, or scope expansion not explicitly authorized by the user.

## Validate proportionately

- Prove deterministic schema generation.
- Prove schema drift detection.
- Prove valid and invalid evidence instances.
- Prove home-relative path constraint.

Report assertions and process exit status separately. A nonzero command is diagnostic evidence, not a passing gate.

## Guard known risks

- Guard against Moving evidence instances that must remain audit context.
- Guard against Creating an invalid shared top-level pending directory.
- Guard against Duplicating a shared schema into several candidates.
- Guard against Leaving stale provenance after a move.
- Guard against Treating a schema instance and its schema definition as the same artifact class.

## Load resources

- Read `references/approach.md` before applying this variant's design.
- Read `references/schema-generation-contract.md` when its named contract is load-bearing.
- Run `scripts/generate_evidence_schema.py` for the deterministic operation it owns; use its `--self-test` before relying on it.
