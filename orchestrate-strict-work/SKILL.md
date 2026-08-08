---
name: orchestrate-strict-work
description: "Coordinate subagents for `strict*` ecosystem work only when the user explicitly requests subagents, agents, delegation, waves, orchestration, parallel research, full-history forks, implementer/verifier pairs, or a specified agent budget. Use to preserve full context, bounded ownership, wave barriers, verification closure, and parent accountability. Do not invoke this skill as permission to delegate an ordinary task."
---

# Orchestrate Strict Work

Delegation changes who performs authorized work; it does not expand what the user authorized. The root remains accountable for scope, evidence, integration, and completion.

## Confirm delegation authority

Do not spawn merely because work is large, difficult, or parallelizable. Confirm the user requested delegation and extract:

- total agent budget and concurrency limit;
- model or effort requirements;
- whether the user explicitly requires context isolation; otherwise use a full-history fork;
- worker, researcher, implementer, reviewer, verifier, or adversarial roles;
- current wave, owned scopes, shared surfaces, and dependency order;
- allowed writes, commands, commits, and external actions;
- stop, pause, resume, and completion rules.

Current explicit instructions override historical defaults. A user may require fresh agents in one task and explicit resume in another.

## Use full-history forks by default

When the user requests agents, delegation, waves, orchestration, or parallel work, give each worker the full available conversation history unless the user explicitly requests an isolated context for that worker. Do not require a second request for full history.

- Use the harness's current full-history option, such as `fork_context: true`, `fork_turns: "all"`, or its exact equivalent; these names are examples, not durable field requirements.
- Do not override model, reasoning effort, service tier, or agent type unless the user explicitly requests a different value.
- Treat the worker as a worker, not a recursive orchestrator.
- Do not rely on inherited history to establish role or scope.
- If a spawn attempt rejects explicit overrides that conflict with full-history inheritance, retry with the full-history setting and the self-contained assignment only; do not silently fall back to isolation.

## Write a self-contained assignment packet

Every worker prompt must state:

- wave and worker role;
- objective and concrete deliverable;
- shared architectural context and settled decisions;
- exact owned paths or read scope;
- exact non-owned and forbidden paths/actions;
- prohibition on reverting or absorbing sibling/user work;
- whether nested agents are forbidden;
- sibling coordination and collision rules;
- authorized verification commands and required working directory;
- commit, push, network, and external-system authority;
- stop conditions and escalation conditions;
- final handoff fields, including changed files, evidence, commands, exit states, blockers, and report path.

The parent cannot grant a worker authority it does not hold.

## Schedule dependency-aware waves

- Parallelize only independent work.
- Give each writer non-overlapping ownership or an explicit shared-file protocol.
- Batch independent read-only calls or workers when the harness supports it.
- Do not waste agent budget on tiny tasks the root can finish more reliably.
- Do not duplicate a worker's assigned work at the root because the worker is slow.
- Keep each worker's semantic assignment single-purpose for its lifetime: use a follow-up only to continue, correct, or refine the same owned slice, and launch a fresh worker for an unrelated assignment even when the earlier worker is idle or complete.
- Do not prepare or start the next wave while a current-wave worker, fix, gate, or handoff remains open.
- Keep one orchestration plane. Workers must not launch shell-level or nested agents unless explicitly authorized.

At compaction or resume, restate the current wave, completed boundary, active workers, exact next event, and hard prohibitions from source artifacts.

## Verify only closed snapshots

A verifier may start only when:

- every dependent implementer has ended its edit loop;
- all required worker gates and handoffs are complete;
- no worker remains reachable with pending fixes;
- the root has integrated current files;
- the snapshot and verification scope are named.

Any post-verdict edit voids the verdict for the changed snapshot. Run a fresh review when required.

When verifier and fixer roles are separate:

1. Verifier reports only.
2. Root validates findings against source and authorized command output.
3. Authorized fixer edits.
4. A fresh verifier checks the resulting closed snapshot.

Do not let a verifier quietly remediate “unmasked” findings.

## Integrate at the root

- Read worker reports and inspect their current artifacts.
- Do not accept a completion claim, test count, or verdict as proof by itself.
- Resolve overlaps against the approved owner model.
- Preserve user and sibling changes.
- Run only the authorized wave boundary.
- Advance only on the user-defined event.
- Commit at a wave boundary only when the user authorized both the boundary and commit.

Honor `STOP` or pause immediately. Do not launch one last check, replacement worker, or cleanup action.

## Final orchestration report

State:

- agents launched versus budget;
- family/wave ownership and completion;
- files or reports produced;
- worker commands and exact gate states;
- whether the verified snapshot was closed;
- unresolved findings and their owner;
- whether any worker, commit, or external action remains active.
