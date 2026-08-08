---
name: resolve-managed-goal-artifacts
description: "Resolve an exact harness-managed goal artifact from a structured goal objective without coupling harness state to skill package topology. Use when a completion hook or resumed workflow must resolve the exact file designated by a structured goal objective or typed goal artifact."
---

# Resolve Managed Goal Artifacts

Apply the `variant-003-typed-goal-artifact` design without silently merging it with sibling approaches.

## Preserve authority

- Treat this nested package as pending review until the user separately authorizes promotion and enablement.
- Preserve run-specific evidence in the canonical repository scratchpad and keep reusable product resources in this package.
- Do not register hooks, edit Codex source, change configuration, synchronize installations, stage unrelated work, or publish as an implied consequence of using this skill.
- Render paths beneath the user home as `~/...` and invoke environment-selected tools instead of hard-coded interpreter paths.

## Apply this design

Read a versioned managed_objective_artifacts list from the successful goal response, require exactly one supported file for the completion handoff, validate its containment and existence, and use objective prose only for human display.

Use this sequence:

1. Identify the authority source and exact input facts before making a policy decision.
2. Apply only the contract documented in `references/approach.md` and its directly named resources.
3. Emit the checked condition, expected value, received value, and stable outcome whenever the design can fail.
4. Keep machine-readable output valid and separate from explanatory prose when a harness schema controls stdout.
5. Stop before any activation, synchronization, external mutation, or scope expansion not explicitly authorized by the user.

## Validate proportionately

- Prove zero, one, and multiple artifact records.
- Prove legacy objective-only response.
- Prove resume serialization.
- Prove pasted text and future non-text artifact kinds.

Report assertions and process exit status separately. A nonzero command is diagnostic evidence, not a passing gate.

## Guard known risks

- Guard against Trusting arbitrary objective paths outside the managed attachments root.
- Guard against Treating custom CODEX_HOME as equivalent to a package location.
- Guard against Schema version skew between Codex and hook packages.
- Guard against Overfitting the current pasted-text wrapper wording.
- Guard against Retaining the installation-relative approach even though it is known to be fragile.

## Load resources

- Read `references/approach.md` before applying this variant's design.
- Read `references/migration-and-resume.md` when its named contract is load-bearing.
- Read `references/typed-goal-artifact-contract.md` when its named contract is load-bearing.
