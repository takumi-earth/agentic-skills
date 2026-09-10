---
name: enforce-semantic-transform-contracts
description: "Inventory and plan migration of parsed-source transformations that rely on fixed paths, marker gates, rendered fragments, full bodies, fingerprints, hashes, regexes, first-match mutation, or textual fallbacks. Use when a bounded lexical inventory is explicitly requested; produce review leads and owner dispositions without rewriting source."
---

# Enforce Semantic Transform Contracts

Collect lexical review leads within the selected scope. An ordinary change to shared machinery does not automatically require an inventory.

## Collect a bounded inventory

Run the scanner only on explicitly selected source roots:

```bash
python3 scripts/inventory_transform_debt.py --repo <repository> --root <source-root>
```

Read [the inventory schema](references/inventory-schema.md) before adjudicating results. The scanner records file, line, signal class, excerpt, and a source-snapshot-local evidence key. Use `--output <inventory.json>` only when the task requires a persisted inventory. Its matches are leads, never proof that a mechanism is wrong or that a rewrite is authorized.

## Complete owner dispositions

For each caller whose disposition the authorized review requires, record in the existing task context the typed owner, complete semantic scope, target query, smallest rewrite, postcondition, cardinality, current mechanism, and one of `keep`, `narrow`, `move`, `replace`, `remove`, or `blocked-by-decision`. Name the movement, decoy, ambiguity, drift, post-state, and replay evidence that would close migration.

Follow `$design-semantic-source-transforms` for migration order: remove explicitly rejected reusable mechanisms first and rebuild affected capabilities through typed contracts. Preserve valid transaction and index infrastructure. This scanner does not prescribe a separate migration gate or replacement ledger.

## Keep analysis inert

This inventory does not authorize source edits, dependency changes, test deletion, staging, commits, or activation. Use the semantic production and adaptive-test owners in the implementation phase selected by the user.
