---
name: resolve-managed-goal-artifacts
description: "Resolve an exact harness-managed goal artifact from objective prose without coupling harness state to skill package topology. Use when a lifecycle hook or resumed workflow must identify one regular attachments artifact through inherited CODEX_HOME; do not use package location, objective paths, or hook output to infer the trusted runtime root."
---

# Resolve Managed Goal Artifacts

Apply the `variant-001-environment-root` design without silently merging it with sibling approaches.

## Preserve authority

- Treat this nested package as pending review until the user separately authorizes promotion and enablement.
- Preserve run-specific evidence in the canonical repository scratchpad and keep reusable product resources in this package.
- Do not register hooks, edit Codex source, change configuration, synchronize installations, stage unrelated work, or publish as an implied consequence of using this skill.
- Render paths beneath the user home as `~/...` and invoke environment-selected tools instead of hard-coded interpreter paths.

## Apply this design

Read inherited `CODEX_HOME` and fall back to `~/.codex` only when the variable is absent. Treat an empty or unusable configured root as `invalid-runtime-root`; never replace it with the fallback.

Use objective prose only to identify filename- and extension-agnostic path references. Require exactly one canonical `attachments/<uuid>/<filename>` path beneath the trusted root, reject traversal and symlink escape, and require a regular non-symlink file.

Return a side-effect-free `GoalArtifactResolution`-equivalent result with `status`, `stage`, `code`, `condition`, safe `expected` and `received` values, `candidate_count`, and optional `artifact`. Use `resolved-exact-artifact` for success and these failure codes:

- `invalid-runtime-root`;
- `objective-not-text`;
- `no-managed-artifact-reference`;
- `ambiguous-managed-artifacts`;
- `attachments-root-mismatch`;
- `managed-path-shape`;
- `artifact-not-file`.

Keep hook-envelope rendering outside this resolver. The operation must make no writes and return the same result for the same objective, environment, and filesystem state.

Use this sequence:

1. Identify the authority source and exact input facts before making a policy decision.
2. Apply only the contract documented in `references/approach.md` and its directly named resources.
3. Emit the checked condition, expected value, received value, and stable outcome whenever the design can fail.
4. Keep machine-readable output valid and separate from explanatory prose when a harness schema controls stdout.
5. Stop before any activation, synchronization, external mutation, or scope expansion not explicitly authorized by the user.

## Validate proportionately

- Prove custom CODEX_HOME positive fixture.
- Prove unset CODEX_HOME ~/.codex fallback fixture.
- Prove empty, missing, relative, and non-directory CODEX_HOME negatives.
- Prove non-text, missing, and ambiguous objective-reference negatives.
- Prove invalid UUID, traversal, non-file, direct-symlink, and symlink-escape negatives.
- Prove repeat-call determinism and filename/extension independence.

Report assertions and process exit status separately. A nonzero command is diagnostic evidence, not a passing gate.

## Guard known risks

- Guard against Trusting arbitrary objective paths outside the managed attachments root.
- Guard against Treating custom CODEX_HOME as equivalent to a package location.
- Guard against Letting one concurrent hook write resolver state for another hook.
- Guard against Overfitting the current pasted-text wrapper wording.
- Guard against Retaining the installation-relative approach even though it is known to be fragile.

## Load resources

- Read `references/approach.md` before applying this variant's design.
- Read `references/resolution-contract.md` when its named contract is load-bearing.
- Run `scripts/resolve_goal_artifact.py` for the deterministic operation it owns; use its `--self-test` before relying on it.
