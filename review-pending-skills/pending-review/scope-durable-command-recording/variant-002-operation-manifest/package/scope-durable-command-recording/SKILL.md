---
name: scope-durable-command-recording
description: "Specify an operation-manifest adapter for the existing command recorder when the authorized task requires recoverable command evidence. Use for manifest and recorder reconciliation; ordinary reads, focused checks, status answers, and validation do not require a manifest."
---

# Scope Durable Command Recording

This package contains a schema and reconciled implementation specification, not an executable runner. `$filesystem-git-observability` owns the existing recorder. Preserve this variant's pre-execution declaration without duplicating that recorder or invoking unsupported flags.

## Preserve authority

- Treat this nested package as pending review until the user separately authorizes promotion and enablement.
- Create run-specific evidence in the canonical repository scratchpad only when the authorized task requires it; keep reusable product resources in this package.
- Do not register hooks, edit Codex source, change configuration, synchronize installations, stage unrelated work, or publish as an implied consequence of using this skill.
- Render paths beneath the user home as `~/...` and invoke environment-selected tools instead of hard-coded interpreter paths.

## Apply this design

Declare `cwd`, inputs, exact `argv`, expected conditions, operation outputs, report path, purpose, and timeout. Read `references/runner-contract.md` for the exact mapping to the existing recorder and its unsupported capabilities before proposing execution. A declaration grants neither execution nor persistence authority and cannot enforce arbitrary child-process effects.

Use this sequence:

1. Identify the authority source and exact input facts before making a policy decision.
2. Apply only the contract documented in `references/approach.md` and its directly named resources.
3. Emit the checked condition, expected value, received value, and stable outcome whenever the design can fail.
4. Keep machine-readable output valid and separate from explanatory prose when a harness schema controls stdout.
5. Stop before any activation, synchronization, external mutation, or scope expansion not explicitly authorized by the user.

## Validate proportionately

- Prove exact argv preservation.
- Prove home-path normalization.
- Distinguish declared outputs from an implemented effect boundary.
- Prove passive read exemption.
- Prove nonzero diagnostic reporting.

Report assertions and process exit status separately. A nonzero command is diagnostic evidence, not a passing gate.

## Guard known risks

- Apply durable recording when the authorized task requires recoverable evidence.
- Preserve direct reads and focused checks without automatic manifests or reports.
- Treat recorded observations as evidence, not authorization or proof of procedure correctness.

## Load resources

- Read `references/approach.md` before applying this variant's design.
- Read `references/runner-contract.md` when its named contract is load-bearing.
