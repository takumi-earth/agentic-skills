# Prepared Authority Handoff Matrix

## Field-level matrix

Use the rows relevant to the affected edge in existing task context; this table is an aid, not a mandatory persisted packet.

| Question | Relevant answer |
|---|---|
| What raw representation enters preparation? | Exact schema or model version and missing, legacy, or canonical fields |
| Who interprets it? | Parser, schema engine, planner, normalizer, or compiler owner |
| What prepared field becomes canonical? | Exact accessor or typed value |
| Which raw reads remain valid? | Only unrelated facts not owned by preparation |
| What is the first consumer? | Exact orchestration operation |
| What barrier protects the effect? | Exact phase before the relevant target writes, including any legitimate earlier preparation effects |
| Which mutation is protected? | Exact repository, file, or external effect whose absence failure must establish |
| Which later observations carry the value? | Work reports, service calls, outcomes, persistence |
| Can production reach an unresolved input? | Constructible missing-authority condition and typed error, or the derivation that makes that branch unreachable |
| What cleanup and recovery follow failure? | Exact order and retained artifacts |

## Protecting evidence

### Migrated positive

- Use a raw fixture that truly lacks the forward field.
- Exercise the same preparation and complete orchestration path as production.
- Assert the prepared value at the first consumer and every downstream attribution point.
- Assert the complete phase and cleanup boundary when those are load-bearing.

### Unresolved negative

- Use this case only when a constructible production input can lack the required authority. Preserve unconditional valid derivation when that is production's contract.
- Remove every legitimate authority source from the real raw input.
- Let failure occur at the earliest production selection boundary.
- Assert the exact typed error and path.
- Assert that the named target writes or protected mutation phase did not begin. Preserve legitimate earlier preparation, restoration, cleanup, and recovery effects instead of claiming that no effect occurred anywhere.

## Counterfactual

If orchestration rereads raw input after preparation, valid legacy input can fail despite successful migration. If the negative test fabricates an impossible prepared object, it proves only the test seam and not the production failure barrier.
