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
- task-required evidence categories, each mapped to actual test identifiers;
- whether substantive product behavior requires separate product-owner tests.

Never serialize a complete upstream body, token signature, hash, regex, or expected path as semantic identity.

## Validate structure

Run:

```bash
python3 scripts/validate_contract.py <declaration.json>
```

The dependency-free CLI evaluates the keywords used by the packaged schema and reports `condition`, `expected`, and `received` for structural defects. It exits `1` for invalid declarations and `2` for unreadable or malformed input. The packaged tests additionally use `jsonschema` to compare structural results. It rejects hint misses that suppress the authoritative query and outcome sets missing ambiguity, mixed-state, postcondition-failure, or replay-failure states.

## Evidence and cross-field checks

`evidence.metamorphic_cases` maps each category required by the actual testing contract to a nonempty array of actual test identifiers; identifiers need not equal category names. Semantic review checks category selection against the task, rather than imposing literal case names on every transformation. `product_behavior_required` declares whether substantive product behavior needs separate evidence. Only when true must `product_owner_tests` be nonempty. The declaration must reflect the controlling contract; choosing false does not waive a real behavioral obligation.

The schema owns field types, unknown-field rejection, hint rules, required typed outcomes, and conditional evidence requirements. The CLI also checks `cardinality.minimum <= maximum` as an explicit cross-field check beyond the schema. Neither layer checks whether the named tests exist or ran.

## Preserve the semantic boundary

Schema success proves only that required fields and declared polarities exist. It does not prove symbol resolution, correct ownership, minimal mutation, atomicity, or test adequacy. Review those facts against current source and execute authorized behavior-first evidence separately.

Do not generate production source or install a parser dependency from this skill. Stop when the declaration cannot identify the owner without a new user decision.
