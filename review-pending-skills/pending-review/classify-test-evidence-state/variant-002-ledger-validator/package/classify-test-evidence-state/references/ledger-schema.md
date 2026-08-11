# Evidence ledger schema

The validator accepts a JSON object with `schema_version: 1` and a `rows` array.

Each row contains:

- `id`: stable nonempty string;
- `owner`: semantic or product owner;
- `contract`: claimed behavior;
- `state`: one of `declared`, `written`, `compiled`, `executed`, `assertions-passed`, `process-passed`, `focused-gate-passed`, `canonical-gate-passed`, or `unexecuted`;
- `scope`: named command or test scope, or `null` before execution;
- `command`: exact argument list, or `null` before execution;
- `assertions`: `passed`, `failed`, `not-observed`, or `null`;
- `exit_status`: integer or `null`;
- `evidence_locator`: nonempty locator for observed evidence, or `null` when merely declared;
- `timestamp`: ISO-8601 string or `null` before execution;
- `behavioral_closure`: boolean;
- `canonical_scope`: boolean.

`unexecuted` and `written` rows must not claim behavioral closure or carry invented process results. Executed and later states require command, scope, timestamp, and evidence. `process-passed` requires exit `0`; `assertions-passed` requires assertion status `passed`; `canonical-gate-passed` requires `canonical_scope: true` and exit `0`.

The schema validates evidence bookkeeping only. It cannot determine whether the named command was authorized, whether the test observed the right owner, or whether the canonical command is correctly identified.
