---
name: enforce-semantic-transform-contracts
description: "Inventory and plan migration of parsed-source transformations that rely on fixed paths, marker gates, rendered fragments, full bodies, fingerprints, hashes, regexes, first-match mutation, or textual fallbacks. Use before replacing a brittle patch-engine family; produce review leads and owner dispositions without rewriting source."
---

# Enforce Semantic Transform Contracts

Make every brittle caller reviewable before changing shared machinery.

## Collect a bounded inventory

Run the scanner only on explicitly selected source roots:

```bash
python3 scripts/inventory_transform_debt.py --root <source-root> --output <inventory.json>
```

Read [the inventory schema](references/inventory-schema.md) before adjudicating results. The scanner records file, line, signal class, excerpt, and a stable evidence key. Its matches are leads, never proof that a mechanism is wrong or that a rewrite is authorized.

## Complete owner dispositions

For every production caller, add the typed owner, complete semantic scope, target query, smallest rewrite, postcondition, cardinality, current mechanism, and one of `keep`, `narrow`, `move`, `replace`, `remove`, or `blocked-by-decision`. Name the movement, decoy, ambiguity, drift, post-state, and replay evidence that would close migration.

Do not stop at counts or translate bodies into hashes. Port upstream-owned whole-item callers first, preserve valid transaction/index/ledger infrastructure, and retire brittle helpers only after every caller and live test contract has a successor.

## Keep analysis inert

This inventory does not authorize source edits, dependency changes, test deletion, staging, commits, or activation. Use the semantic production and adaptive-test owners in the implementation phase selected by the user.
