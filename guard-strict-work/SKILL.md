---
name: guard-strict-work
description: "Preserve authority, ownership, scope, and completion contracts throughout work in the `strict*` ecosystem. Use for any task in or affecting `strict*`, `rust-template`, `template-rs`, `strict-xtask-*`, a strict-owned fork, or a repository consuming strict ecosystem infrastructure. This is the compact foundation for planning, implementation, verification, documentation, dependency, orchestration, and commit work."
---

# Guard Strict Work

Treat the user's operating contract as task state, not conversational background. Choose owners by capability before choosing files, commands, or local fixes.

## Build the task contract

At intake, extract the smallest contract that can prevent phase drift:

- Objective and concrete end state.
- Active read and write scope, including explicitly excluded paths or repositories.
- Prescribed and prohibited methods.
- Settled ownership, API, compatibility, distribution, and tooling decisions.
- Verification authority, exact accepted commands, and human-only gates.
- Git, index, commit, push, and external-system authority.
- Purpose- and time-scoped exceptions, supersessions, and still-active prohibitions.
- Delegation authority and required worker shape.
- Stop condition and the current phase: answer, diagnose, plan, implement, verify, or commit.

Do not infer a permission from a plan section, repository convention, dirty worktree, surfaced diagnostic, tool result, previous phase, worker request, or “normal workflow.” Only a live user instruction can expand authority.

## Preserve hard boundaries

Apply these rules with low freedom:

- A prohibition remains active until the user changes it.
- A requested method is an acceptance criterion, not a stylistic preference.
- A terminal instruction such as “finish” changes persistence, not action authority.
- An investigation, diagnosis, review, or plan does not authorize edits.
- Implementation does not automatically authorize verification, mutation testing, commits, pushes, or sibling-repository changes.
- A verifier cannot receive repair authority that the parent does not possess.
- Dirty or concurrent state changes merge-safety behavior only. It does not narrow the intended design or authorize cleanup.
- Unexpected changes are evidence of concurrency, not evidence that the agent owns them.
- Never restore, reset, checkout, clean, stage, or unstage unexpected state without explicit authorization for the exact action and targets.

Re-read the contract before moving from research to planning, planning to editing, editing to verification, verification to commit, or one orchestration wave to the next.

When a user message arrives during active work, use `$reconcile-live-steering` before the next effect. Classify whether it overrides, adds, clarifies, supplies diagnostics, reports acceptance, corrects external state, duplicates carried-forward context, or changes authority. A later purpose-bound exception does not erase a broader prohibition outside that purpose, while an explicitly superseded constraint must not be preserved as caution.

After context compaction or rollout continuation, use `$resume-strict-context` before task action. A summary locates authority; it does not replace the complete living goal.

A verification failure that authorizes source changes moves the active phase back to implementation. Close the full authorized correction set before re-entering verification at the ledger's declared restart point.

## Resolve ownership before location

Ask what capability and invariant own the behavior if the current caller, file extension, language, command, and diagnostic name are removed.

Walk outward from the symptom:

1. Identify the observed site and behavior.
2. Find the producer of the shape: generator, macro, parser/model, schema, API, feature boundary, workflow, or harness.
3. Find the product or ecosystem owner responsible for the invariant.
4. Classify each downstream repository as owner, adapter, operational consumer, generated consumer, or test consumer.
5. Change the owner, then converge consumers through the supported workflow.

Do not infer destination architecture from an incomplete starting snapshot. Do not use physical location as proof of semantic ownership. Read [the ownership model](references/ownership-model.md) when the task crosses repository, generator, or adapter boundaries.

## Route by task type

Use the specialized skill whose trigger matches the active phase:

- `$plan-strict-work` for plans, architecture, migrations, and source-backed approval artifacts.
- `$implement-strict-work` for edits, structural remediation, refactors, and capability-preserving convergence.
- `$verify-strict-work` for any allowed or prohibited correctness, acceptance, lint, test, coverage, mutation, or formatting command.
- `$commit-strict-work` only after explicit commit authority.
- `$orchestrate-strict-work` only after the user explicitly requests subagents, delegation, waves, or orchestration.
- `$document-strict-work` for documentation, research artifacts, generated guidance, fragments, snapshots, or configuration commentary.
- `$upgrade-strict-dependencies` for dependency, manifest, fork, patch, edition, toolchain, or runtime-version migrations.
- `$maintain-living-goal` when a user-designated goal or plan is the active implementation contract.
- `$protect-causal-architecture` when phase order, authority epochs, mutation barriers, cleanup, persistence, or protecting tests could change.
- `$review-strict-dependency-candidates` before selecting or adding a third-party crate or runtime dependency.
- `$design-command-observability` when a command can block, fan out, make policy decisions, or must preserve payload output while reporting progress.

Task-specific skills refine this foundation. None may expand the task contract.

## Report completion precisely

Keep these states separate:

- Implementation is complete.
- Authorized diagnostics passed or failed.
- The canonical acceptance gate passed or was not run.
- The index or commit operation completed.
- External publication, push, or deployment completed.

Never collapse them into “done,” “green,” “verified,” or “clean.” If the user owns verification, report implementation state and wait for their evidence. If a blocker belongs to another owner or requires new authority, report the exact boundary rather than working around it.
