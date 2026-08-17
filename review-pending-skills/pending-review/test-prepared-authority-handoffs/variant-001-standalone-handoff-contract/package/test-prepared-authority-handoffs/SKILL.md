---
name: test-prepared-authority-handoffs
description: "Plan, implement, or review workflows where an engine parses, validates, migrates, normalizes, or prepares canonical state that downstream orchestration must consume. Use when later code rereads stale raw input for a field already owned by a prepared result, when schema tests pass but a complete workflow still fails, or when positive migrated-input and negative prewrite evidence are needed. Do not use for unrelated immutable input facts that the prepared result does not own or for a single pure conversion with no authority epoch."
---

# Test Prepared Authority Handoffs

Make the prepared result the authority for every field it canonically owns.

## Map the handoff

Read [the handoff matrix](references/handoff-matrix.md), then record:

1. raw input and its valid pre-preparation facts;
2. preparation owner and validation or migration rules;
3. canonical prepared result and field-level authority;
4. first downstream consumer;
5. last effect-free barrier and first mutator;
6. every later consumer of the prepared field;
7. cleanup and persistence ordering.

Do not treat a prepared object as authoritative for unrelated fields it does not expose or interpret.

## Remove stale rediscovery

- After preparation succeeds, obtain each canonically interpreted field from the prepared result.
- Do not rerun legacy precedence, migration fallbacks, or raw-input inference in orchestration.
- Pass the selected value unchanged through every typed work observation and outcome that attributes behavior to it.
- Preserve the existing typed failure when the prepared field can genuinely be absent.
- Do not broaden a public constructor or fabricate an impossible prepared value merely to reach a defensive branch.

## Prove both polarities

Add workflow-level evidence, not only engine-unit evidence:

- Positive: raw input lacks the forward field, preparation legitimately produces it, the complete workflow succeeds, and every downstream observation uses the prepared value.
- Negative: no explicit, migratable, historical, checkpoint, or native authority exists, so the workflow returns the exact typed error before every target write or mutation epoch.

Use real role-correct fixtures for file-consuming boundaries. Do not force the negative case by synthesizing a stage-less or authority-less prepared object that production cannot construct.

## Preserve barriers

The handoff fix must not move preflight after mutation, persist selected authority early, skip cleanup, or weaken recovery semantics. Compare the current and proposed authority, barrier, mutation, cleanup, and persistence chains before editing.

