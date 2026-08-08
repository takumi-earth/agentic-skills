---
name: resolve-managed-goal-artifacts
description: "Resolve an exact harness-managed goal artifact from a structured goal objective without coupling harness state to skill package topology. Use when a completion hook or resumed workflow must resolve the exact file designated by a structured goal objective or typed goal artifact."
---

# Resolve Managed Goal Artifacts

Apply the `variant-001-environment-root` design without silently merging it with sibling approaches.

## Preserve authority

- Treat this nested package as pending review until the user separately authorizes promotion and enablement.
- Preserve run-specific evidence in the canonical repository scratchpad and keep reusable product resources in this package.
- Do not register hooks, edit Codex source, change configuration, synchronize installations, stage unrelated work, or publish as an implied consequence of using this skill.
- Render paths beneath the user home as `~/...` and invoke environment-selected tools instead of hard-coded interpreter paths.

## Apply this design

Read CODEX_HOME from the inherited hook environment, expand and canonicalize it, resolve only exact regular files under its attachments directory, reject ambiguity and symlink escape, and return a typed result naming condition, expected root, received root, candidate count, and candidate path.

Use this sequence:

1. Identify the authority source and exact input facts before making a policy decision.
2. Apply only the contract documented in `references/approach.md` and its directly named resources.
3. Emit the checked condition, expected value, received value, and stable outcome whenever the design can fail.
4. Keep machine-readable output valid and separate from explanatory prose when a harness schema controls stdout.
5. Stop before any activation, synchronization, external mutation, or scope expansion not explicitly authorized by the user.

## Validate proportionately

- Prove custom CODEX_HOME positive fixture.
- Prove unset CODEX_HOME ~/.codex fallback fixture.
- Prove missing, ambiguous, invalid UUID, non-file, and symlink-escape negatives.
- Prove canonical-direct, copied, and symlinked package execution parity.

Report assertions and process exit status separately. A nonzero command is diagnostic evidence, not a passing gate.

## Guard known risks

- Guard against Trusting arbitrary objective paths outside the managed attachments root.
- Guard against Treating custom CODEX_HOME as equivalent to a package location.
- Guard against Schema version skew between Codex and hook packages.
- Guard against Overfitting the current pasted-text wrapper wording.
- Guard against Retaining the installation-relative approach even though it is known to be fragile.

## Load resources

- Read `references/approach.md` before applying this variant's design.
- Read `references/resolution-contract.md` when its named contract is load-bearing.
- Run `scripts/resolve_goal_artifact.py` for the deterministic operation it owns; use its `--self-test` before relying on it.
