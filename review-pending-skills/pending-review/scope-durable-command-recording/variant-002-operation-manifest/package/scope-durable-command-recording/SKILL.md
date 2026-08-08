---
name: scope-durable-command-recording
description: "Require durable scripts and persisted reports for substantive computation, mutation, and evidence production without wrapping passive instruction or source reads in unnecessary task scripts. Use when planning command execution under a durable-script mandate and deciding whether a direct read is sufficient or a repeatable auditable operation is required."
---

# Scope Durable Command Recording

Apply the `variant-002-operation-manifest` design without silently merging it with sibling approaches.

## Preserve authority

- Treat this nested package as pending review until the user separately authorizes promotion and enablement.
- Preserve run-specific evidence in the canonical repository scratchpad and keep reusable product resources in this package.
- Do not register hooks, edit Codex source, change configuration, synchronize installations, stage unrelated work, or publish as an implied consequence of using this skill.
- Render paths beneath the user home as `~/...` and invoke environment-selected tools instead of hard-coded interpreter paths.

## Apply this design

Persist cwd, inputs, exact argv, expected conditions, outputs, and timeout before execution; keep passive reads outside the manifest; refuse shell interpolation and unlisted side effects.

Use this sequence:

1. Identify the authority source and exact input facts before making a policy decision.
2. Apply only the contract documented in `references/approach.md` and its directly named resources.
3. Emit the checked condition, expected value, received value, and stable outcome whenever the design can fail.
4. Keep machine-readable output valid and separate from explanatory prose when a harness schema controls stdout.
5. Stop before any activation, synchronization, external mutation, or scope expansion not explicitly authorized by the user.

## Validate proportionately

- Prove exact argv preservation.
- Prove home-path normalization.
- Prove undeclared output rejection.
- Prove passive read exemption.
- Prove nonzero diagnostic reporting.

Report assertions and process exit status separately. A nonzero command is diagnostic evidence, not a passing gate.

## Guard known risks

- Guard against Calling a substantive source selection a passive read to evade durability.
- Guard against Wrapping trivial reads and obscuring intent.
- Guard against Treating a persisted report as proof that a flawed procedure is correct.
- Guard against Retaining the rejected record-every-command variant without marking it inactive.

## Load resources

- Read `references/approach.md` before applying this variant's design.
- Read `references/runner-contract.md` when its named contract is load-bearing.
