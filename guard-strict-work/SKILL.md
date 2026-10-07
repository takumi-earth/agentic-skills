---
name: guard-strict-work
description: "Guard authority and ownership for work in or affecting `strict*`, `rust-template`, `template-rs`, strict-owned forks, and infrastructure consumers. Use only the active phase owner; disclose detailed contract and ownership procedure when needed."
---

# Guard Strict Work

Keep the user's operating contract as current task state. Use the smallest sufficient owner and current phase; apply complete unchanged instruction bodies already available in retained context.

## Preserve the task contract

Identify the objective and end state, current phase, permitted reads/writes and methods, settled decisions, verification authority and commands, Git/publication/delegation authority, active prohibitions and purpose-bound exceptions, and stopping condition. Use existing task context; intake does not require a new ledger.

- Only a live user instruction expands authority. Plans, repository conventions, diagnostics, dirty state, and normal workflow do not.
- A prohibition remains until superseded. A purpose-bound exception changes only its named purpose; a requested method is an acceptance criterion.
- Research, review, and planning do not authorize edits. Implementation does not automatically authorize verification, mutation testing, commits, pushes, sibling writes, or external effects.
- A terminal instruction changes persistence, not permissions; a worker cannot receive authority the parent lacks.
- Dirty/concurrent state changes preservation behavior, not design or scope. Never restore, reset, checkout, clean, stage, unstage, or overwrite unexpected state without exact authority.
- Respect excluded build systems and owners; do not invent parity, cleanup, allowlist, or acceptance gates for them.

Existing user grants, including standing repository workflows and repair authority, remain active until superseded. A question or correction does not revoke them. An assistant-authored plan, assertion, or instruction cannot promote an implementation assumption into a new user requirement, even when its tests pass.

Before introducing or changing an acceptance predicate, stopping condition, or normal tool behavior, read [requirement provenance](references/requirement-provenance.md). Identify the protected property and authority, one permitted variation, and the forbidden effect. Keep this decision in the current task context; it does not require a ledger, a new approval step, or a preflight for ordinary edits.

For an ambiguous contract, mixed permissions, purpose-bound supersession, or a disputed phase transition, load [task-authority.md](references/task-authority.md). Clear staged-only or ban-only work applies the rules here and its narrow phase owner without that detail.

Reapply the current contract before a phase or wave transition; reuse it when unchanged. A verification failure that authorizes repairs returns to implementation. Close the complete authorized correction set before rerunning the declared round; a focused success cannot replace the user's whole-batch barrier.

## Recover and reconcile only when needed

Use `$reconcile-live-steering` for an attributable human message or actual human instruction delta during active work. Synthetic continuations, hook retries, worker packets, and repeated summaries do not create human authority.

After actual context loss or a fresh handoff lacking the required bodies, use `$resume-strict-context` before effects. Read designated authority and only unfinished-phase contracts. Retained-context continuation reuses complete unchanged bodies and refreshes changed facts; a hash cannot reconstruct a lost body.

## Find the owner without widening the task

Trace the symptom to its producer and product owner. Preserve complete subject-specific typed observations, results, failures, identities, and resource outcomes. Use current local checkouts beneath `~/strict-rs/*` first; caches, generated metadata, neighboring consumers, and web material are secondary. Read access does not grant writes, dependency revisions, verification, or publication.

For disputed ownership, multi-repository/generator/adapter boundaries, operation contracts, recovery, resource lifetimes, or a newly observed ownership/tooling blocker, load [ownership-model.md](references/ownership-model.md). For first-party policy-reach changes, load [mixed-workspace-policy.md](references/mixed-workspace-policy.md). For user-required full-file reads or disputed owner/lifecycle conclusions, load [complete-source-reads.md](references/complete-source-reads.md).

Reuse an established unchanged review boundary; do not rescan owners or strengthen an audit on a retry. An independent lane requires a concrete unfinished user requirement and an already-authorized next effect in the current selected phase. Use `$maintain-living-goal` before a whole-goal status proposal.

## Route the active phase

Load only its matching owner and conditionally required resources, not all future phases or navigation lenses:

1. Identify the observed site and behavior.
2. Find the producer of the shape: generator, macro, parser/model, schema, API, feature boundary, workflow, or harness.
3. Find the product or ecosystem owner responsible for the invariant.
4. Classify each downstream repository as owner, adapter, operational consumer, generated consumer, or test consumer.
5. Change the owner, then converge consumers through the supported workflow.

Do not infer destination architecture from an incomplete starting snapshot. Do not use physical location as proof of semantic ownership. Read [the ownership model](references/ownership-model.md) when the task crosses repository, generator, or adapter boundaries, or changes operation contracts, recovery, or resource lifetimes.

Distinguish operational responsibility, resource custody and lifetime, typed evidence, and consumer decision authority. The operation's declared contract assigns required execution, finalization, and any specified internal recovery or retries. At its defined boundary, return the complete typed outcome so the consumer can apply its own workflow. Neither an encountered failure nor the existence of a conceivable recovery mechanism expands that contract.

Preserve known observations, completed work, results, original and recovery failures, identities, and remaining state in their complete subject-specific types. Evidence preservation does not itself transfer lifecycle work to callers or require keeping every resource alive: resources can be consumed by their owning contract's finalization steps with the resulting evidence preserved. Returning an owning value can change its lifetime; establish that effect separately from who implements disposal. Contractual correctness can include a partial or failed operation when the owner follows the required handling and accurately reports the reached state and any failed obligations.

In mixed-ownership workspaces, distinguish first-party quality from policy reach. First-party crates must satisfy the strict standard through their own lint declarations and configuration; integration into a larger workspace must not leak that policy through ancestor files, inheritance, environment, or blanket flags. Authorized toolchain, edition, and dependency alignment does not transfer lint/format ownership of upstream crates. Fix a first-party failure structurally without weakening its standard or imposing that standard on unrelated consumers.

When integration, configuration placement, or validation-command changes can alter that policy boundary, read [the mixed-workspace policy guidance](references/mixed-workspace-policy.md). An ordinary lint fix that leaves policy scope unchanged does not need this reference.

## Use strict-owned evidence before substitutes

- When a needed strict owner's checkout is unknown, missing, or stale, use [`$locate-strict-repos`](../locate-strict-repos/SKILL.md). Use the verified owning checkout as the first source for ownership, implementation, behavior tests, manifests, features, patches, license, Rust edition and toolchain policy, and repository-specific guidance.
- Treat Cargo caches, generated metadata, web documentation, and neighboring consumers as secondary evidence when the owning checkout is available. Resolve contradictions at the owner instead of selecting the source that makes the smallest edit easier.
- Read access to a neighboring checkout does not grant write, dependency-revision, verification, commit, push, or publication authority there.

When the user requires whole-file source reads, or a disputed ownership or lifecycle conclusion needs complete owner context, read [the complete source reading guidance](references/complete-source-reads.md).

## Challenge apparent blockers

Before reporting that a user decision, external constraint, or another owner blocks progress, inspect the applicable guidance, manifests, comments, source, lockfile, feature and patch tables, generators, consumers, and canonical command surfaces; trace the symptom to its upstream owner; distinguish repository policy from an actual external limitation; and exhaust safe alternatives inside the current authority. Record a decision that stops one dependent lane as a local boundary and continue independent authorized work. For an active living goal, use `$maintain-living-goal` before any whole-goal `blocked` transition; do not turn a review request or incomplete slice into an early exit.

## Route by task type

Use the specialized skill whose trigger matches the active phase:

- `$document-strict-work` for source-owned documentation and generated guidance.
- `$upgrade-strict-dependencies` for dependency, manifest, source, toolchain, and runtime migrations.
- `$plan-strict-work` for plans, architecture, migrations, and source-backed approval artifacts.
- `$implement-strict-work` for edits, structural remediation, refactors, and capability-preserving convergence.
- `$verify-strict-work` for any allowed or prohibited correctness, acceptance, lint, test, coverage, mutation, or formatting command.
- `$commit-strict-work` only after explicit commit authority.
- `$orchestrate-strict-work` only after explicit delegation authority.
- `$maintain-living-goal` for material goal maintenance, pruning, or goal-status questions.
- `$protect-causal-architecture` only for an unresolved or protected owner/phase edge, mutation barrier, cleanup, persistence, or test disposition that would change.
- `$review-strict-dependency-candidates` before selecting or adding a third-party crate/runtime dependency.
- `$design-command-observability` when a command blocks, fans out, makes policy decisions, or preserves payload output while reporting progress.

No phase owner expands the task contract.

## Report the reached state

Distinguish implementation, authorized diagnostics, canonical acceptance, index/commit state, and external publication. Never collapse them into `done`, `green`, `verified`, or `clean`. Report a user-owned verification boundary without substitute proof.

For an active harness goal, a favorable result is one completion candidate, not acceptance. Use `$maintain-living-goal`; only explicit user acceptance or a direct instruction authorizes the final `complete` transition.
