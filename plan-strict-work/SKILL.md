---
name: plan-strict-work
description: "Create source-backed implementation plans for `strict*` ecosystem architecture, refactors, upgrades, migrations, extractions, crate splits, generated workflows, and multi-repository convergence. Use when the user asks to plan, design, investigate for a plan, review a proposed plan, or prepare an implementation handoff. Settle load-bearing user decisions without turning ordinary implementation discovery into a preflight audit. Planning remains read-only unless the user separately authorizes edits."
---

# Plan Strict Work

Produce a plan that settles load-bearing ownership and behavior choices while leaving ordinary local implementation discovery to implementation. Do not use planning detail as later execution authority.

When the plan becomes a user-designated living implementation contract, maintain it through `$maintain-living-goal`. Use `$protect-causal-architecture` only when the plan changes a user-protected or genuinely disputed causal edge. Do not load it merely because the plan has several phases, mutations, validations, or cleanup steps.

## Establish the planning contract

Carry forward the active task contract from `$guard-strict-work`, especially:

- exact objective and target end state;
- source and repository scope;
- settled decisions that must not be reopened;
- decisions the user explicitly reserves;
- verification, commit, and delegation boundaries;
- required primary sources and direct-reading requirements.

If the user asks only for a plan, do not edit, generate, format, verify, stage, or commit.

## Research before deciding

Inspect current source, repository guidance, manifests, generators, consumers, and canonical command surfaces before finalizing the plan.

- Resolve cheap, local facts directly instead of asking the user.
- Use primary sources for current dependency or external API facts.
- Read source first-hand when the user requires full reads; delegated summaries are not equivalent.
- Distinguish current mechanics from intended destination.
- Treat ignored plans, stale comments, incomplete forks, dead-looking modules, and current diagnostics as evidence to investigate, not product intent.
- Search current decisions before presenting an architectural fork. Reopen a settled choice only when current evidence contradicts it, and state that contradiction.

## Resolve ownership first

For every behavior, identify:

- product or ecosystem owner;
- generator, macro, parser/model, API, workflow, or harness that produces the shape;
- adapters and operational consumers;
- generated outputs and their source workflow;
- public and compatibility boundaries;
- positive and negative behavior owned by each layer.

Do not choose an owner from the current file, caller, language, workspace glob, command, or failing diagnostic.

## Close only load-bearing decisions

Name only the categories that materially affect this implementation:

- exact repositories, paths, modules, and non-owned surfaces;
- final public and internal types, signatures, commands, schemas, configuration keys, and error behavior;
- dependency versions or version-selection policy, provenance, features, patches, and forks;
- data and control flow, including invalid-input and failure paths;
- each load-bearing authority, mutation, barrier, downstream consumer, counterfactual regression, and positive/negative behavior polarity;
- capability-preservation and compatibility stance;
- generator or source-of-truth workflow and expected generated fallout;
- migration order and a complete end-state matrix for every in-scope consumer;
- exact removals, renames, and stale vocabulary;
- positive and negative behavior tests at the owning boundary;
- canonical formatting and verification commands, authority, runtime matrix,
  stop conditions, and every generated file, executable, staging root, or
  runtime dependency required for each command to be runnable in its stated phase;
- deterministic trigger isolation, causal evidence, and restoration steps when
  an acceptance test must attribute an outcome to one of several live mechanisms;
- orchestration waves, non-overlapping ownership, and handoff fields when explicitly requested;
- commit boundaries only when the user requests commit planning.

Resolve wording ambiguity only when it would change behavior, ownership, scope, compatibility, or an external effect. Do not turn harmless conditional wording into a mechanical audit.

Do not compress a selected multi-phase sequence into outcome-only wording such as “reach a fixed point,” “plan statically,” or “refresh when needed.” Final-state equivalence does not prove that information was available at the same time or that failure ordering is preserved.

## Surface only genuine user decisions

Ask only when all of these are true:

1. The choice materially changes behavior, compatibility, ownership, scope, or external state.
2. Current source and durable guidance do not settle it.
3. A reasonable assumption would risk divergence.
4. The user has not already selected it.

Present complete alternatives and consequences. Do not hide consequential subchoices behind a selected top-level option. Do not cite assistant-authored “Decision N” labels as user authorization.

If a proposal changes a protected causal edge that the user has not already authorized, state the current edge, proposed edge, affected owner, counterfactual, and evidence needed for the choice. Stop only dependent effects and ask once. If the user already authorized that exact change, plan it directly without another approval gate.

## Plan for convergence, not passes

For multi-repository or replacement work:

- Build a matrix of owner, old surface, new surface, consumer migration, verification, and completion state.
- Follow the user-selected migration order. When an invalid reusable mechanism would otherwise remain precedent, remove its API first, let compile failures identify affected capabilities, and use Git history only on demand.
- Separate publication order from working-tree completeness.
- Keep every in-scope consumer coherent at the promised stage boundary.
- Preserve product capability unless the user explicitly chooses breakage or retirement.

## Handoff standard

The final plan must prevent the implementer from having to make user-owned architecture choices. It need not reproduce routine repository discovery, command hygiene, or workflow rules already owned by current guidance. State:

- what becomes true;
- why each owner is correct;
- exact edit and removal scope;
- behavioral evidence to add;
- allowed commands and gates;
- explicit non-goals and prohibitions;
- stop and escalation conditions.

Do not call a plan implementation-ready while it leaves a load-bearing user choice unresolved. Ordinary source navigation and local implementation discovery are not plan defects.
