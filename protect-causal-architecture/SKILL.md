---
name: protect-causal-architecture
description: "Protect user-selected causal ordering and ownership when a change genuinely alters who may mutate what, when authority becomes valid, or which barrier makes later effects safe. Use for disputed multi-stage authority, generation or cleanup order, assistant-authored status being treated as authority, or legacy precedent conflicting with an explicit architecture. Do not use as a preflight for ordinary implementation, to create an audit artifact by default, or for one source transformation with no disputed causal edge; use `$design-semantic-source-transforms` instead."
---

# Protect Causal Architecture

Preserve load-bearing causal relationships without turning implementation into a governance project.

## Start from current authority

Use this order:

1. Current explicit user decisions.
2. Direct source and external facts within the authorized scope.
3. Accepted behavior evidence.
4. Current partial implementation.
5. Names, convenience, precedent, and implementation size.

Assistant-authored goals, plans, status, and audits record authority; they do not create it. Do not cite partial code plus an assistant-authored status update as mutually supporting authority.

If the user already authorized the exact architectural change, implement it. Do not require another approval, a baseline selection exercise, a causal packet, or a durable audit before starting. Pause only when the next effect would decide an owner, ordering, authority, or retirement question the user has not resolved.

## Record only the disputed causal contract

When a real causal edge is disputed or easy to lose, state the minimum facts needed to preserve it:

- the authority or owner before the step;
- the allowed mutation and resulting state;
- the required predecessor or barrier;
- the next consumer;
- the concrete failure caused by bypassing or reordering the edge;
- the positive behavior and forbidden-shortcut evidence.

Keep this record in the existing plan, goal, issue, or code contract. Do not create a separate scratch artifact unless the user requested one or the authorized workflow intrinsically requires durable recovery state. Expand to a complete multi-stage chain only when several interacting edges would otherwise remain ambiguous.

## Reject architectural lookalikes

When the requirement is semantic, adaptive, structural, or location-independent, keep target identity, discovery scope, syntax anchoring, load-bearing drift, mutation, and postcondition separate.

- An AST-bounded write proves a syntax boundary, not semantic discovery.
- A normalized token stream, body hash, regex, or encoded snapshot remains complete source ownership when unrelated changes invalidate it.
- A path, marker, version, or expected module is only a hint when its miss still runs the authoritative full-scope query.
- A field named `semantic_owner` is diagnostic unless the implementation actually resolves or discovers that owner.
- Rendering parsed source back to text does not make a substring, equality, or snapshot assertion structural.

Legacy implementation and passing local tests are evidence of current behavior, not permission to reproduce an explicitly rejected mechanism. When the user has declared a mechanism obsolete, remove its reusable API and test escape hatches first. Let compile failures identify capabilities that need rebuilding, and consult Git history only for a specific capability after defining its replacement contract.

Use `$design-semantic-source-transforms` for production transformation design and `$test-adaptive-source-transforms` for its evidence.

## Gate only unresolved architecture

Do not stop already-authorized implementation merely because it changes a mutator, barrier, cleanup step, or test. Gate work only when the requested implementation would force an unresolved architectural choice.

For an unresolved choice:

1. State the current and proposed causal edge.
2. Name the affected owner and artifact state.
3. Give the concrete counterfactual regression.
4. Name the evidence that would distinguish the choices.
5. Stop only the effects that depend on that decision and ask once.

When the user corrects an authority or test disposition, retract the affected downstream statements and effects. Search farther only when the same invalid premise may have been duplicated elsewhere; do not turn every correction into a whole-goal audit.

## Protect behavior without creating a parity project

- Removing a brittle assertion mechanism does not retire the behavior it attempted to protect.
- A changed implementation strategy does not make a still-live behavior obsolete.
- Map touched tests to equal-or-stronger typed or owner-level evidence as they are rewritten.
- Retire a contract only when its production capability was actually removed.
- Never invent replacement behavior to satisfy bookkeeping.
- Require evidence to observe the semantic owner or causal effect, not a marker, copied body, aggregate count, or rendered source.

Use `$verify-test-parity` only when the user explicitly requests a comprehensive parity audit. If a broad rewrite cannot be closed safely through local touched-test mappings, report that concrete gap and ask whether the user wants the comprehensive audit; do not start it automatically. Never invoke it merely because a plan mentions it or because one brittle test is being replaced.

## Preserve compacted causal state proportionally

After compaction, reconstruct only the genuinely protected multi-stage chain before changing one of its disputed edges. Ordinary implementation does not require a closed-book reconstruction exercise.

Outcome-only phrases such as “reach a fixed point” or “refresh when needed” are insufficient when ordering is load-bearing; replace them with the one missing owner, predecessor, barrier, or postcondition.
