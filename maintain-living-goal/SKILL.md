---
name: maintain-living-goal
description: "Maintain a user-designated goal, plan, or specification as a minimal living implementation contract. Use before and after complete implementation slices, during pruning, when updating current status or blockers, and whenever a long-running task must keep repository-specific architecture intact without accumulating chronology."
---

# Maintain Living Goal

Keep the goal sufficient to resume correctly from the file alone. Move generic execution procedure into skills; retain repository-specific authority, causal design, current facts, open decisions, and acceptance work.

## Resolve and structure the authority

When the active harness supplies an exact living-goal path, treat that path as the sole living authority for the session and read it directly. Do not enumerate, compare, timestamp, size, or select among sibling attachments because an older path appears in conversation, memory, or a compaction summary. Consult another attachment only when the user or active harness explicitly designates it as historical comparison input. If two sources are explicitly designated as active authorities, stop and ask which governs before editing either. Only when the harness supplies no active path may the user's latest explicit designation or current goal metadata resolve the living artifact; never choose a similarly named repository file by convenience.

Keep only the sections the task needs, normally:

- objective and completion boundary;
- protected user-selected or source-derived causal architecture;
- current repository and external-authority facts;
- exact active implementation slice and later ordered slices;
- unresolved user decisions, their affected causal lanes, and any currently observed whole-goal impasse;
- behavior evidence, generated work, and canonical verification still required.

Do not copy generic commit, verification, dependency-review, compaction, or slice procedure into every goal when a triggered user-level skill supplies it. Do not remove repository-specific rationale merely because a skill contains the general rule.

## Execute one complete slice

1. Investigate the complete owning boundary and every behavior required for one coherent correction.
2. Reconcile the goal to the discovered factual state before source edits. Record settled decisions, exact owner, inputs, outputs, failure order, and remaining behavior evidence.
3. Implement the complete slice through its owner.
4. Resolve the complete authorized diagnostic batch for that slice before rerunning a gate.
5. Run the real formatter when authorized, then repeat relevant symbol scans after formatting.
6. Prune the goal to present-tense fact and the next unfinished slice.
7. Perform the closed-book reconstruction and contradiction sweep below.
8. Investigate the next slice only after the current slice and goal state are closed.

If work repeats without closing a slice or producing a new owner-level decision, record the repeated condition and challenge whether another authorized, causally independent slice can still make meaningful progress. Stop the affected loop without converting it into a whole-goal blocker. Use the whole-goal state protocol below only when every remaining in-scope lane depends on the same unresolved condition.

## Prune with an attributable replacement

Classify each statement before changing it:

- **Procedural chronology:** remove when it no longer affects current work.
- **Mutable status:** rewrite to current fact.
- **Supporting evidence:** retain only while it supports an active decision, blocker, or acceptance obligation.
- **Protected causal contract:** preserve through `$protect-causal-architecture`; change only after explicit supersession.

Touch protected packets individually. Never replace a whole section when that prevents statement-for-statement attribution.

Implementation, passing tests, formatting, generation, and canonical verification may change a protected packet's mutable status and rewrite planned wording into present-tense repository fact. They do not delete the packet's authority, causal reason, predecessor/successor order, barrier, counterfactual failure, forbidden shortcut, or positive/negative evidence. Remove a protected field only after an explicit user decision supersedes it with an equal-or-stronger packet.

After pruning, reconstruct from the goal alone:

- every authority read;
- every artifact-mutating lane;
- every refresh, validation, generation, checkpoint, cleanup, and persistence barrier;
- the state handed between them;
- the counterfactual failure and positive/negative test for each load-bearing edge;
- the exact next slice.

Then scan the whole goal for contradictory counts, vocabulary, ownership, phase order, source authority, and test intent. Repair ambiguity before implementation continues.

## Govern whole-goal state without punting

- A protected-edge review, dependency choice, external decision, or user review stops only the work that causally depends on it. Record that local boundary and continue every meaningful authorized lane that is independent of it. A pending decision, stopped slice, or desire for clarification is not by itself a whole-goal blocker.
- Before proposing `blocked`, enumerate the unfinished requirements and authorized lanes, inspect current state, exhaust safe in-scope alternatives, and show that none can make meaningful progress without the same user input or external-state change. Follow the harness-owned repeated-blocker audit: the same genuine whole-goal impasse must survive at least three consecutive goal turns, including the original or resumed turn as the harness defines it. Use each continuation to challenge the premature-blocker hypothesis; never manufacture, subdivide, or count turns merely to reach the threshold.
- When the objective appears satisfied, treat that judgment as a falsifiable completion hypothesis. Produce a self-contained requirement-by-requirement candidate audit that maps every deliverable, invariant, command, gate, and user instruction to authoritative current evidence and identifies missing, weak, indirect, contradictory, or unrun evidence. Do not shrink the objective around completed work.
- The user exclusively decides whether the candidate audit establishes achievement. Do not call `update_goal(status: "complete")`, declare the goal achieved, or treat acceptance as a ceremonial bit flip unless the user explicitly accepts the audit or directly instructs that exact transition. If review identifies omitted or weak work, return to ordinary continuation. Any substantive later change invalidates the prior audit until it is refreshed and accepted again.
- Do not use low remaining context, elapsed time, a passing partial source, an unchallenged final answer, or absence of newly discovered work as a blocked or completion criterion.
- Update cross-project memory only when the user explicitly authorizes it, and never substitute memory notes for complete repository-specific goal state.

## Use the packaged Codex Stop adapter

`scripts/active_goal_stop_hook.py` is an optional Codex-specific adapter that requests one same-turn anti-punting continuation while the thread goal is `active`. It reads `goals_1.sqlite` by the hook input's `session_id`, uses a parameterized read-only query, and emits only schema-valid `Stop` JSON. It does not parse the transcript, edit the goal, count a continuation as another goal turn, or decide goal status.

- Keep artifact creation and activation as separate authorities. Creating, maintaining, or testing the packaged script does not authorize adding it to a harness hook configuration.
- On the first `Stop` pass of an active goal, emit `{"decision":"block","reason":"..."}` with the continuation audit. On `stop_hook_active: true`, malformed or non-`Stop` input, a missing or unreadable database, an absent thread row, or any non-active status, emit `{}` and exit successfully.
- When the user authorizes activation, add the command as an independent `Stop` handler and preserve every existing lifecycle event, matcher group, and handler. `Stop` ignores matchers; do not rewrite an unrelated `PostToolUse` or other hook as part of registration.
- Treat the adapter as continuation hardening, not a completion-transition guard. It cannot prevent an unauthorized `update_goal(status: "complete")` call that occurs before turn end.
- After changing the adapter, run `python3 scripts/test_active_goal_stop_hook.py` from this package and then validate the complete skill package.

After compaction, use `$resume-strict-context` before applying this workflow.
