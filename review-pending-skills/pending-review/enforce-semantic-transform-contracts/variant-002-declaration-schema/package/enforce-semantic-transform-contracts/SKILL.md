---
name: enforce-semantic-transform-contracts
description: "Author or validate machine-readable contracts for adaptive parsed-source transformations. Use when a patch engine or codemod needs stable IDs, semantic owners and scopes, typed candidate outcomes, hint fallback rules, postconditions, replay, and evidence links checked before implementation. Do not treat schema validity as proof of semantic correctness."
---

# Enforce Semantic Transform Contracts

Make declaration omissions mechanically visible while keeping semantic review with the transformation owner.

## Write one declaration per transformation

Conform declarations to [the bundled schema](references/transformation-contract.schema.json). Include:

- stable `id` and typed `owner`;
- complete semantic `scope` and `query`;
- load-bearing `precondition` and minimal `rewrite`;
- semantic `postcondition` and `cardinality`;
- typed outcome names;
- every discovery hint and its full-query miss behavior;
- movement, decoy, ambiguity, drift, post-state, and replay evidence identifiers.

Never serialize a complete upstream body, token signature, hash, regex, or expected path as semantic identity.

## Validate structure

Run:

```bash
python3 scripts/validate_contract.py <declaration.json>
```

The validator reports `condition`, `expected`, and `received` for structural defects and exits nonzero. It rejects hint misses that suppress the authoritative query and outcome sets missing ambiguity, mixed-state, postcondition-failure, or replay-failure states.

## Preserve the semantic boundary

Schema success proves only that required fields and declared polarities exist. It does not prove symbol resolution, correct ownership, minimal mutation, atomicity, or test adequacy. Review those facts against current source and execute authorized behavior-first evidence separately.

Do not generate production source or install a parser dependency from this skill. Stop when the declaration cannot identify the owner without a new user decision.
