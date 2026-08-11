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

## Prevent self-authorizing goal edits

A goal edit records authority or evidence that already exists; it never creates authority for later implementation merely because the assistant wrote it into the goal.

Before each edit, classify every changed statement and retain its primary provenance:

- **Explicit user selection:** cite the user message or already protected packet that selected it.
- **Carried protected contract:** preserve its existing authority, causal edges, counterfactual, and evidence without changing their meaning.
- **Source-derived mutable fact:** cite the direct source, command, or external-authority observation and keep it factual; it may describe implementation status but may not add a target decision.
- **Assistant proposal:** keep it visibly proposed and non-authoritative. If it changes architecture, tests, a baseline, or an allowed mutator, route it through `$protect-causal-architecture` and wait for explicit user selection before dependent effects.

Never label an assistant-derived design “decision-complete,” rewrite it as implementation fact, or use it as the premise for source/test edits unless its authority can be traced past assistant-authored goal text to an explicit user decision or protected/source-derived contract. The goal itself is not independent corroboration for a statement the assistant inserted.

Mutable status cannot:

- change a parity or historical baseline;
- retire a production capability or protecting test;
- turn a removed architecture into a replacement-test obligation;
- add an authority read, mutator, barrier, compatibility surface, or migration;
- reinterpret implementation drift as the selected target.

When a status update would do any of those things, stop the dependent edit. Record the current packet, proposed packet, primary authority, affected tests, and counterfactual for user review. Do not implement the proposal first and then reconcile the goal to legitimize it.

When the user corrects a baseline, architecture, or test disposition, treat every downstream assistant-authored goal statement and dependent source/test edit as untrusted until a provenance audit revalidates or retracts it. Apply the correction across the whole goal in the same pass; a local wording fix that leaves a contradictory status claim is not a completed correction.

For the concrete failure that established these rules, load [the autonomous goal-edit regression](references/autonomous-goal-edit-regression.md) when auditing goal provenance, parity-baseline drift, or a correction that may have left dependent statements alive.

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

For each removal or rewrite, retain an attributable record containing the old statement, its provenance class, the replacement statement, its provenance class, and the primary evidence that permits the change. A later pass must be able to distinguish user selection from assistant mechanics without consulting current source as intent.

Implementation, passing tests, formatting, generation, and canonical verification may change a protected packet's mutable status and rewrite planned wording into present-tense repository fact. They do not delete the packet's authority, causal reason, predecessor/successor order, barrier, counterfactual failure, forbidden shortcut, or positive/negative evidence. Remove a protected field only after an explicit user decision supersedes it with an equal-or-stronger packet.

After pruning, reconstruct from the goal alone:

- every authority read;
- every artifact-mutating lane;
- every refresh, validation, generation, checkpoint, cleanup, and persistence barrier;
- the state handed between them;
- the counterfactual failure and positive/negative test for each load-bearing edge;
- the exact next slice.

Then scan the whole goal for contradictory counts, vocabulary, ownership, phase order, source authority, and test intent. Repair ambiguity before implementation continues.

The contradiction sweep must also compare every historical/parity baseline and every replacement-versus-retirement disposition across protected architecture, mutable status, remaining slices, and acceptance evidence. A correct baseline in one paragraph does not neutralize a conflicting assistant-authored claim elsewhere.

## Govern whole-goal state without punting

- A protected-edge review, dependency choice, external decision, or user review stops only the work that causally depends on it. Record that local boundary and continue every meaningful authorized lane that is independent of it. A pending decision, stopped slice, or desire for clarification is not by itself a whole-goal blocker.
- Before proposing `blocked`, enumerate the unfinished requirements and authorized lanes, inspect current state, exhaust safe in-scope alternatives, and show that none can make meaningful progress without the same user input or external-state change. Follow the harness-owned repeated-blocker audit: the same genuine whole-goal impasse must survive at least three consecutive goal turns, including the original or resumed turn as the harness defines it. Use each continuation to challenge the premature-blocker hypothesis; never manufacture, subdivide, or count turns merely to reach the threshold.
- When the objective appears satisfied, treat that judgment as a falsifiable completion hypothesis. Produce a self-contained requirement-by-requirement candidate audit that maps every deliverable, invariant, command, gate, and user instruction to authoritative current evidence and identifies missing, weak, indirect, contradictory, or unrun evidence. Do not shrink the objective around completed work.
- The user exclusively decides whether the candidate audit establishes achievement. Do not call `update_goal(status: "complete")`, declare the goal achieved, or treat acceptance as a ceremonial bit flip unless the user explicitly accepts the audit or directly instructs that exact transition. If review identifies omitted or weak work, return to ordinary continuation. Any substantive later change invalidates the prior audit until it is refreshed and accepted again.
- Do not use low remaining context, elapsed time, a passing partial source, an unchallenged final answer, or absence of newly discovered work as a blocked or completion criterion.
- Update cross-project memory only when the user explicitly authorizes it, and never substitute memory notes for complete repository-specific goal state.

## Use the packaged completion-handoff adapter

`scripts/goal_artifact_resolution.py` is the pure shared resolver for managed goal artifacts. It reads inherited `CODEX_HOME`, falls back to `~/.codex` only when that variable is absent, and returns a deterministic typed result without writing state or emitting a hook envelope. It resolves exactly one regular non-symlink `attachments/<uuid>/<filename>` artifact named by objective prose after canonical containment checks. Package-resource lookup is distinct from harness-state authority; never derive `CODEX_HOME` from this package's resolved location.

`scripts/goal_completion_handoff_hook.py` is the independent Codex `PostToolUse` adapter for successful `update_goal(status="complete")` events. It does not require a transcript. On resolution success, it injects goal-specific delimiters, structured completion accounting, and the model-owned write-and-re-read barrier for preserving the ordinary final-ready result exactly once. It does not write the artifact itself or name, invoke, or own any later automatic review. On typed resolution failure, it preserves the successful completion result, renders the condition, expected value, received value, stage, code, and candidate count, and directs the ordinary completion response while withholding downstream post-completion work whose durable prerequisite is missing.

- Keep success code `resolved-exact-artifact` and failure codes `invalid-runtime-root`, `objective-not-text`, `no-managed-artifact-reference`, `ambiguous-managed-artifacts`, `attachments-root-mismatch`, `managed-path-shape`, and `artifact-not-file` stable.
- Keep every emitted hook response to one valid `PostToolUse` `hookSpecificOutput` envelope, process status `0`, and empty stderr. Non-completion and malformed events are silent no-ops.
- Keep automatic post-completion skill review under `$auto-skill-enhancer`; it may independently consume the pure resolver as a declared sibling-package resource but cannot own or reconstruct this lifecycle handoff.
- Keep artifact creation, hook registration, and hook trust as separate authorities. Creating, maintaining, or testing these scripts does not authorize adding or trusting them in a harness configuration.
- After changing either resource, run `python3 scripts/test_goal_completion_handoff_hook.py` from this package and then validate the complete skill package.

## Use the packaged Codex Stop adapter

`scripts/active_goal_stop_hook.py` is an optional Codex-specific adapter that requests one same-turn anti-punting continuation while the thread goal is `active`. It reads `goals_1.sqlite` by the hook input's `session_id`, uses a parameterized read-only query, and emits only schema-valid `Stop` JSON. It does not parse the transcript, edit the goal, count a continuation as another goal turn, or decide goal status.

- Keep artifact creation and activation as separate authorities. Creating, maintaining, or testing the packaged script does not authorize adding it to a harness hook configuration.
- On the first `Stop` pass of an active goal, emit `{"decision":"block","reason":"..."}` with the continuation audit. On `stop_hook_active: true`, malformed or non-`Stop` input, a missing or unreadable database, an absent thread row, or any non-active status, emit `{}` and exit successfully.
- When the user authorizes activation, add the command as an independent `Stop` handler and preserve every existing lifecycle event, matcher group, and handler. `Stop` ignores matchers; do not rewrite an unrelated `PostToolUse` or other hook as part of registration.
- Treat the adapter as continuation hardening, not a completion-transition guard. It cannot prevent an unauthorized `update_goal(status: "complete")` call that occurs before turn end.
- After changing the adapter, run `python3 scripts/test_active_goal_stop_hook.py` from this package and then validate the complete skill package.

After compaction, use `$resume-strict-context` before applying this workflow.
