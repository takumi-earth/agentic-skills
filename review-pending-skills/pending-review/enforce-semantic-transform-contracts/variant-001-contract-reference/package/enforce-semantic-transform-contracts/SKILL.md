---
name: enforce-semantic-transform-contracts
description: "Specify or review parsed-source transformations that must survive formatting, relocation, unrelated upstream edits, and equivalent spellings. Use when AST, CST, HIR, codemod, patch-engine, or fork-adaptation work may be using fixed paths, markers, full bodies, fingerprints, hashes, or rendered fragments as target identity. Do not use solely for exact repository-owned generated output."
---

# Enforce Semantic Transform Contracts

Require semantic identity and the smallest owned delta instead of an encoded snapshot of the current upstream implementation.

## Declare the complete contract

Record a stable transformation ID, typed owner, complete permitted scope, semantic query, load-bearing precondition, minimal syntax rewrite, semantic postcondition, and candidate cardinality. Keep identity, discovery, syntax anchoring, drift detection, mutation, and postcondition separate.

Read [the contract checklist](references/contract-checklist.md) before accepting a design or implementation.

## Classify before mutation

Use this order:

```text
index complete scope
    -> query and classify every candidate
    -> enforce cardinality and state compatibility
    -> plan the complete edit set
    -> apply in an isolated transaction
    -> refresh semantic state
    -> verify the postcondition
    -> replay and require an empty delta
    -> publish atomically
```

Distinguish pre-state, post-state, incompatible, absent, ambiguous, mixed-state, postcondition-failed, and non-idempotent outcomes. Every non-applying result must preserve the authoritative workspace byte-for-byte.

## Reject disguised snapshots

- Treat paths, versions, markers, and spellings as hints only; a miss must run the complete query.
- Do not use full source bodies, normalized tokens, fingerprints, hashes, regexes, or templates as applicability authority.
- Do not call a diagnostic `semantic_owner` field semantic discovery.
- Do not let a Git or textual patch run silently after semantic discovery fails.
- Permit exact whole-item ownership only when the repository explicitly owns the complete emitted or vendored item and exact content is the contract.

## Require counterfactual evidence

Prove target movement, unrelated extension, stale-path decoys, two genuine candidates, real load-bearing drift, recognized post-state, and replay without changing the transformation declaration. Use typed structural and product-owner assertions; rendered source is not a structural oracle.

Stop when semantic ownership is ambiguous, the required resolver surface is unauthorized, or the only proposed identity is a path or complete body.
