# Evidence ledger schema

The validator accepts a JSON object with `schema_version: 1` and a `rows` array.

Each row contains:

- `id`: stable nonempty string;
- `owner`: semantic or product owner;
- `contract`: claimed behavior;
- `state`: one of `declared`, `written`, `compiled`, `executed`, `assertions-passed`, `process-passed`, `focused-gate-passed`, `canonical-gate-passed`, or `unexecuted`;
- `scope`: named command or test scope, or `null` before execution;
- `command`: exact argument list with a nonempty executable and string arguments (including legitimate empty arguments), or `null` before command execution;
- `assertions`: `passed`, `failed`, `not-observed`, or `null`;
- `exit_status`: integer or `null`;
- `evidence_locator`: nonempty locator for observed evidence, or `null` when merely declared;
- `timestamp`: valid ISO-8601 calendar instant with timezone, or `null` before command execution;
- `behavioral_closure`: boolean;
- `canonical_scope`: boolean.
- `acceptance`: optional `null` or an object with exactly `criteria` (nonempty description of the actual gate contract) and `result` (`passed`, `failed`, or `not-observed`); required with a passed result for a passing gate or behavioral closure.

`schema_version` is the integer `1`, never a Boolean. Only `declared` may omit an evidence locator; written and observed rows identify their source evidence. `unexecuted` and `written` cannot claim behavioral closure, process results, or observed acceptance. `compiled` requires a successful build command, scope, timestamp, and evidence, with assertions unobserved; this is not test-body execution.

Executed states require command, scope, timestamp, evidence, and exit status. `process-passed` requires exit `0`; `assertions-passed` requires assertions `passed` and may coexist with a nonzero process exit when closure is false. Passing focused/canonical gates require explicit passed acceptance and reject failed assertions even without a closure claim. A non-behavioral gate may have unobserved assertions when its declared criteria warrant that; behavioral closure additionally requires passed assertions and process success. Canonical scope remains a separate required claim for `canonical-gate-passed`.

The validator preserves exact supplied command arguments and reads no referenced evidence. Caller-owned source/configuration/run identity and current applicability remain necessary; a later verification prohibition does not erase earlier applicable observations. Use existing records rather than creating a ledger merely to classify evidence.

The schema validates evidence bookkeeping only. It cannot determine whether the named command was authorized, whether the test observed the right owner, or whether the canonical command is correctly identified.
