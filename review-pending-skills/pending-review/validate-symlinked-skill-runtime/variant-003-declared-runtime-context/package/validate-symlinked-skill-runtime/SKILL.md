---
name: validate-symlinked-skill-runtime
description: "Separate package-resource location from harness-runtime state and validate copied, symlinked, and canonical-direct skill execution as equivalent deployment topologies. Use when a user-level skill includes executable resources that read or write harness state and may be installed by copy or symlink."
---

# Validate Symlinked Skill Runtime

Apply the `variant-003-declared-runtime-context` design without silently merging it with sibling approaches.

## Preserve authority

- Treat this nested package as pending review until the user separately authorizes promotion and enablement.
- Preserve run-specific evidence in the canonical repository scratchpad and keep reusable product resources in this package.
- Do not register hooks, edit Codex source, change configuration, synchronize installations, stage unrelated work, or publish as an implied consequence of using this skill.
- Render paths beneath the user home as `~/...` and invoke environment-selected tools instead of hard-coded interpreter paths.

## Apply this design

Define a small context manifest listing CODEX_HOME, canonical skill repository, scratchpad root, and package root ownership; validate required values before entry-point execution; do not infer missing values by walking parents.

Use this sequence:

1. Identify the authority source and exact input facts before making a policy decision.
2. Apply only the contract documented in `references/approach.md` and its directly named resources.
3. Emit the checked condition, expected value, received value, and stable outcome whenever the design can fail.
4. Keep machine-readable output valid and separate from explanatory prose when a harness schema controls stdout.
5. Stop before any activation, synchronization, external mutation, or scope expansion not explicitly authorized by the user.

## Validate proportionately

- Prove complete manifest.
- Prove missing authority.
- Prove conflicting environment and manifest.
- Prove schema version skew.

Report assertions and process exit status separately. A nonzero command is diagnostic evidence, not a passing gate.

## Guard known risks

- Guard against Running arbitrary package scripts during synchronization.
- Guard against Confusing canonical repository location with harness installation root.
- Guard against Overconstraining stateless packages with unnecessary topology tests.
- Guard against Retaining lexical-path inference as a known weak variant.

## Load resources

- Read `references/approach.md` before applying this variant's design.
- Read `references/launcher-contract.md` when its named contract is load-bearing.
