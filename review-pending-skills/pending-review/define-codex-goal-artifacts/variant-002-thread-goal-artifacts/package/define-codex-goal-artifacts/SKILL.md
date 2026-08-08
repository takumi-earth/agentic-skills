---
name: define-codex-goal-artifacts
description: "Define a typed Codex protocol contract for managed goal-objective artifacts so hooks do not recover machine state from display prose. Use when planning or implementing Codex goal/protocol changes involving pasted objective files, goal persistence, or PostToolUse consumers."
---

# Define Codex Goal Artifacts

Apply the `variant-002-thread-goal-artifacts` design without silently merging it with sibling approaches.

## Preserve authority

- Treat this nested package as pending review until the user separately authorizes promotion and enablement.
- Preserve run-specific evidence in the canonical repository scratchpad and keep reusable product resources in this package.
- Do not register hooks, edit Codex source, change configuration, synchronize installations, stage unrelated work, or publish as an implied consequence of using this skill.
- Render paths beneath the user home as `~/...` and invoke environment-selected tools instead of hard-coded interpreter paths.

## Apply this design

Add a versioned artifact list to internal goal state and protocol ThreadGoal, preserve it across update, pause, resume, and completion, and expose it in tool responses without changing human objective text.

Use this sequence:

1. Identify the authority source and exact input facts before making a policy decision.
2. Apply only the contract documented in `references/approach.md` and its directly named resources.
3. Emit the checked condition, expected value, received value, and stable outcome whenever the design can fail.
4. Keep machine-readable output valid and separate from explanatory prose when a harness schema controls stdout.
5. Stop before any activation, synchronization, external mutation, or scope expansion not explicitly authorized by the user.

## Validate proportionately

- Prove goal create/update response.
- Prove resume persistence.
- Prove legacy serialized state.
- Prove multiple artifact kinds.
- Prove deleted artifact behavior.

Report assertions and process exit status separately. A nonzero command is diagnostic evidence, not a passing gate.

## Guard known risks

- Guard against Protocol migration and version skew.
- Guard against Persisting host-specific paths across machines.
- Guard against Ambiguous ownership between goal state and hook event context.
- Guard against Expanding scope beyond the confirmed hook bug.

## Load resources

- Read `references/approach.md` before applying this variant's design.
- Read `references/persistence-migration.md` when its named contract is load-bearing.
- Read `references/thread-goal-artifact-schema.md` when its named contract is load-bearing.
