---
name: protect-causal-architecture
description: "Preserve causal architecture across multi-phase workflows and refactors. Use when a design has multiple authority epochs, mutations, refresh or validation barriers, checkpoints, child attempts, generation passes, cleanup or persistence order; when changing that order; or when current code is being used to call protecting tests stale."
---

# Protect Causal Architecture

Final-state equivalence is not causal equivalence. Preserve why each authority becomes available, which owner may mutate which artifact, and which barrier makes that state safe for the next consumer.

## Build reconstructable packets

Record every load-bearing invariant as one packet containing:

1. **Authority and input state:** exact source of truth and artifact state before the step.
2. **Allowed mutation and output state:** semantic owner, permitted effect, and exact state produced.
3. **Causal order:** required predecessor and successor.
4. **Barrier:** refresh, validation, checkpoint, generation, cleanup, or persistence condition that makes the output usable.
5. **Counterfactual:** concrete regression caused by omission, reordering, narrowing, or late mutation.
6. **Behavior evidence:** positive path and negative forbidden-shortcut tests.

Mark the packet as user-selected or source-derived. Keep it separate from mutable implementation status.

After implementation or verification, update only the packet's mutable status or tense. Passing tests, a favorable audit, reduced process count, and verified repository state do not erase the authority source, causal explanation, ordering, barrier, counterfactual, forbidden shortcut, or positive/negative evidence that make the packet reconstructable.

## Apply the authority hierarchy

Use this order:

1. Current explicit user decision.
2. Protected causal packets.
3. Accepted behavior tests.
4. Current partial implementation.
5. Names, process-count reductions, minimal-change preferences, and implementation convenience.

Do not reverse this order. Partial source is status evidence, not authority to rationalize a new architecture or retire tests that protect the selected design.

Assistant-authored goal text has no independent rank in this hierarchy. Before using a goal statement to authorize production or test changes, trace it to an explicit user decision, an unchanged protected packet, accepted behavior evidence, or direct source-derived fact. If the only provenance is an earlier assistant goal edit, the statement is a proposal or status claim, not authority.

Keep mutable implementation status one-way: primary authority and evidence may update status, but status may never flow back into architecture, baseline selection, capability retirement, or test obligations. Do not implement a proposal and then cite the resulting partial source plus a rewritten goal as mutually supporting evidence.

## Gate architecture changes

Before an edit that changes an authority read, mutator, causal edge, barrier count, child attempt, migration/generation pass, checkpoint, cleanup, or persistence order:

- write the complete current chain;
- write the proposed replacement chain;
- enumerate every altered edge and artifact state;
- explain each counterfactual and affected positive/negative test;
- reconcile the living goal;
- stop every production or generated effect that depends on the disputed edge;
- continue every authorized lane that is causally independent of that edge;
- obtain explicit user approval before production edits.

Record the pending decision as a local causal stop, not an automatic whole-goal blocker. Only when no meaningful in-scope work remains may `$maintain-living-goal` apply the harness-owned repeated-impasse protocol to the whole goal.

Do not use a passing test, fewer processes, static preplanning, performance, naming symmetry, or reduced writes as implicit approval.

The same gate applies when the proposed change is phrased as pruning, status reconciliation, parity closure, or removal of stale tests. Record statement-level provenance before the goal edit. An assistant-derived replacement design remains non-authoritative even when it is written in present tense, called “decision-complete,” or partially implemented.

When the user corrects an authority, historical baseline, or test disposition:

- invalidate every downstream assistant-authored statement and dependent effect that used the superseded premise;
- search the complete goal for contradictory copies, status claims, remaining slices, and acceptance rows;
- retract or revalidate each dependent statement against primary authority;
- stop source and test work until that audit closes.

A correction to one paragraph is insufficient when another paragraph still encodes the invalid premise.

## Protect behavior evidence

- A test is stale only when an explicitly retired production capability makes its observable contract obsolete.
- A changed implementation strategy does not retire the behavior it was meant to preserve.
- A parity baseline is authority, not a convenient comparison point. Do not switch `HEAD^`, `HEAD`, a checkpoint, tag, or release boundary because the current tree makes the inventory smaller or the replacement easier.
- Decompose aggregate removed tests by observable assertion. Map still-live behavior to equal-or-stronger evidence and retire only assertions whose sole production capability was explicitly removed.
- Never invent replacement behavior that recreates a removed architecture merely to give a ledger row a replacement test. Retirement evidence and replacement evidence are distinct dispositions.
- For each edge, test both the required path and the forbidden shortcut, including failure ordering and canonical reruns where relevant.
- Use `$verify-test-parity` before broad test deletion, moves, consolidation, or replacement.

Load [the goal-authority regression](references/goal-authority-regression.md) when an assistant goal edit, baseline correction, or replacement-versus-retirement decision may have changed protecting evidence.

## Reconstruct closed-book

After planning, pruning, or compaction, enumerate the entire sequence from the living goal without consulting source. If two sequences are possible, a packet is missing. Repair the contract before work continues.

Outcome-only phrases such as “reach a fixed point,” “plan statically,” “refresh when needed,” or “already converged” are insufficient unless the complete packet remains reconstructable.
