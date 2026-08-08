---
name: render-hook-decision-failures
description: "Render every hook policy or resolution failure with the exact checked condition, expected value, received value, failure stage, and stable machine-readable code. Use when designing or repairing hooks and commands that make policy decisions or convert structured failures into user-visible context."
---

# Render Hook Decision Failures

Apply the `variant-002-structured-failure-exceptions` design without silently merging it with sibling approaches.

## Preserve authority

- Treat this nested package as pending review until the user separately authorizes promotion and enablement.
- Preserve run-specific evidence in the canonical repository scratchpad and keep reusable product resources in this package.
- Do not register hooks, edit Codex source, change configuration, synchronize installations, stage unrelated work, or publish as an implied consequence of using this skill.
- Render paths beneath the user home as `~/...` and invoke environment-selected tools instead of hard-coded interpreter paths.

## Apply this design

Define a bounded exception hierarchy carrying diagnostic fields, prevent broad exception text from becoming the public contract, and render unexpected exceptions separately from expected policy failures.

Use this sequence:

1. Identify the authority source and exact input facts before making a policy decision.
2. Apply only the contract documented in `references/approach.md` and its directly named resources.
3. Emit the checked condition, expected value, received value, and stable outcome whenever the design can fail.
4. Keep machine-readable output valid and separate from explanatory prose when a harness schema controls stdout.
5. Stop before any activation, synchronization, external mutation, or scope expansion not explicitly authorized by the user.

## Validate proportionately

- Prove expected exception conversion.
- Prove unexpected exception classification.
- Prove no stack trace in hook stdout.
- Prove exact field preservation.

Report assertions and process exit status separately. A nonzero command is diagnostic evidence, not a passing gate.

## Guard known risks

- Guard against Exposing sensitive received values without redaction.
- Guard against Making human messages too verbose for hook context.
- Guard against Allowing unstable exception strings to become machine codes.
- Guard against Assuming stderr is surfaced when the hook exits successfully.

## Load resources

- Read `references/approach.md` before applying this variant's design.
- Read `references/structured-failure-exceptions.md` when its named contract is load-bearing.
