---
name: test-prepared-authority-handoffs
description: "Plan, implement, or review workflows where an engine parses, validates, migrates, normalizes, or prepares canonical state that downstream orchestration must consume. Use when later code rereads stale raw input for a field already owned by a prepared result, when schema tests pass but a complete workflow still fails, or when positive migrated-input and negative prewrite evidence are needed. Do not use for unrelated immutable input facts that the prepared result does not own or for a single pure conversion with no authority epoch."
---

# Test Prepared Authority Handoffs

Make the prepared result the authority for every field it canonically owns.

## Map the handoff

Use [the handoff matrix](references/handoff-matrix.md) for fields and edges affected by the task. Establish the relevant facts in existing task context:

1. raw input and its valid pre-preparation facts;
2. preparation owner and validation or migration rules;
3. canonical prepared result and field-level authority;
4. first downstream consumer;
5. barrier before the relevant target writes or protected mutation phase, including legitimate earlier preparation effects;
6. every later consumer of the prepared field;
7. cleanup and persistence ordering.

Do not treat a prepared object as authoritative for unrelated fields it does not expose or interpret.

Use the existing task's recording contract. This guidance does not require a persisted matrix, a new audit artifact, or renewed approval for an already approved change.

## Remove stale rediscovery

- After preparation succeeds, obtain each canonically interpreted field from the prepared result.
- Do not rerun legacy precedence, migration fallbacks, or raw-input inference in orchestration.
- Pass the selected value unchanged through every typed work observation and outcome that attributes behavior to it.
- Preserve the existing typed failure when the prepared field can genuinely be absent.
- Do not broaden a public constructor or fabricate an impossible prepared value merely to reach a defensive branch.

## Test reachable workflow behavior

Add workflow-level evidence, not only engine-unit evidence:

- Positive: raw input lacks the forward field, preparation legitimately produces it, the complete workflow succeeds, and every downstream observation uses the prepared value.
- Negative, when reachable: construct a real input with no supported explicit, migratable, historical, checkpoint, or native authority, then assert the typed error before the named protected target writes or mutation phase. If production always derives a valid value, preserve that behavior and do not invent a failure branch.

Use role-correct fixtures under the actual scenario contract. Do not force the negative case by synthesizing a stage-less or authority-less prepared object that production cannot construct. Legitimate earlier preparation effects, cleanup, or restoration remain observable and retain their recovery obligations.

## Preserve barriers

The handoff fix must not move preflight after mutation, persist selected authority early, skip cleanup, or weaken recovery semantics. Compare the current and proposed authority, barrier, mutation, cleanup, and persistence chains before editing.
