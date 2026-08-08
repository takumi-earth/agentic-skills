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

## Apply the authority hierarchy

Use this order:

1. Current explicit user decision.
2. Protected causal packets.
3. Accepted behavior tests.
4. Current partial implementation.
5. Names, process-count reductions, minimal-change preferences, and implementation convenience.

Do not reverse this order. Partial source is status evidence, not authority to rationalize a new architecture or retire tests that protect the selected design.

## Gate architecture changes

Before an edit that changes an authority read, mutator, causal edge, barrier count, child attempt, migration/generation pass, checkpoint, cleanup, or persistence order:

- write the complete current chain;
- write the proposed replacement chain;
- enumerate every altered edge and artifact state;
- explain each counterfactual and affected positive/negative test;
- reconcile the living goal;
- mark it blocked;
- obtain explicit user approval before production edits.

Do not use a passing test, fewer processes, static preplanning, performance, naming symmetry, or reduced writes as implicit approval.

## Protect behavior evidence

- A test is stale only when an explicitly retired production capability makes its observable contract obsolete.
- A changed implementation strategy does not retire the behavior it was meant to preserve.
- For each edge, test both the required path and the forbidden shortcut, including failure ordering and canonical reruns where relevant.
- Use `$verify-test-parity` before broad test deletion, moves, consolidation, or replacement.

## Reconstruct closed-book

After planning, pruning, or compaction, enumerate the entire sequence from the living goal without consulting source. If two sequences are possible, a packet is missing. Repair the contract before work continues.

Outcome-only phrases such as “reach a fixed point,” “plan statically,” “refresh when needed,” or “already converged” are insufficient unless the complete packet remains reconstructable.
