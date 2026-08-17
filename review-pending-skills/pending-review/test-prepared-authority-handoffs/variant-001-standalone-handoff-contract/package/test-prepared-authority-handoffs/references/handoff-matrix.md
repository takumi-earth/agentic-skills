# Prepared Authority Handoff Matrix

## Field-level matrix

| Question | Required answer |
|---|---|
| What raw representation enters preparation? | Exact schema or model version and missing, legacy, or canonical fields |
| Who interprets it? | Parser, schema engine, planner, normalizer, or compiler owner |
| What prepared field becomes canonical? | Exact accessor or typed value |
| Which raw reads remain valid? | Only unrelated facts not owned by preparation |
| What is the first consumer? | Exact orchestration operation |
| What is the last effect-free barrier? | Exact phase or typestate boundary |
| What is the first mutation? | Exact repository, file, or external effect |
| Which later observations carry the value? | Work reports, service calls, outcomes, persistence |
| What unresolved input must still fail? | Exact missing-authority condition and typed error |
| What cleanup and recovery follow failure? | Exact order and retained artifacts |

## Protecting evidence

### Migrated positive

- Use a raw fixture that truly lacks the forward field.
- Exercise the same preparation and complete orchestration path as production.
- Assert the prepared value at the first consumer and every downstream attribution point.
- Assert the complete phase and cleanup boundary when those are load-bearing.

### Unresolved negative

- Remove every legitimate authority source from the real raw input.
- Let failure occur at the earliest production selection boundary.
- Assert the exact typed error and path.
- Assert no target write, mutation epoch, restoration attempt, or later phase began.

## Counterfactual

If orchestration rereads raw input after preparation, valid legacy input can fail despite successful migration. If the negative test fabricates an impossible prepared object, it proves only the test seam and not the production failure barrier.

