# Manifest adapter and recorder contract

This is the reconciled implementation specification for `variant-002-operation-manifest`. It does not provide an executable adapter or authorize changing the official recorder.

## Current operational owner

`filesystem-git-observability/scripts/persist_command_report.py` accepts `--output`, `--purpose`, repeated `--input`, optional `--parse-json`, and the command after `--`. It has no `--manifest`, `--cwd`, timeout, condition evaluator, or output enforcement option. Pass exact argument elements; do not interpolate a shell command.

| Manifest field | Current mapping and capability boundary |
| --- | --- |
| `argv` | Pass after `--`, preserving order and empty non-first arguments. The executable must be nonempty. |
| `purpose` | Pass as `--purpose`. |
| `inputs` | Pass as repeated `--input`; the recorder hashes before and after execution. These snapshots do not prove which bytes the child consumed. |
| `report_path` | Pass as `--output`. The recorder also publishes `<name>.started.json` and refuses conflicts. This path is separate from the operation's declared outputs. |
| `parse_json` | When true, select `--parse-json`. Parsing stdout is independent from operation success or acceptance. |
| `cwd` | The recorder inherits its working directory. A future adapter must establish and record the selected directory explicitly. |
| `timeout_seconds` | Unsupported by the current recorder. Implement a deadline and partial-effect result before promising or using timeout enforcement. |
| `expected_conditions` | Declarative until the selected decision owner evaluates actual received facts. Never execute a condition string or substitute its expected value for an observation. |
| `outputs` | A declaration, not a restriction or completeness check. Enforcing an effect boundary requires an implemented owner; a list or post-hoc diff cannot prevent unlisted effects. |

## Publication and outcome semantics

The current recorder hashes inputs, exclusively publishes a started record, launches the child, captures stdout/stderr and process exit, hashes inputs again, and exclusively publishes the final record. JSON publication flushes and syncs the temporary file, then links it into place without replacement. It does not sync the containing directory or promise exactly-once command effects.

The started record precedes child launch. A started record without a final record therefore establishes neither execution nor non-execution. Launch, hashing, and persistence failures can leave this state and currently lack a normalized structured failure contract. Reconcile actual effects before any authorized retry; do not automatically rerun or roll back.

The recorder returns a nonzero child exit; otherwise a requested stdout-JSON parse failure returns `5`, and success returns `0`. It parses an object from the first `{` in stdout. Object parsing and zero exit establish neither passing assertions nor satisfaction of expected conditions.

The current helper serializes raw paths and captured output. A future adapter must implement the presentation contract for designated path fields, including diagnostics, without changing argument identity before execution, corrupting home-neighbor paths, or rewriting original evidence bytes before hashing. Schema validation alone does not normalize paths.

## Authority and planned acceptance cases

Use a manifest only when the authorized task requires recoverable evidence. Ordinary reads, focused checks, status answers, and validation do not require a manifest or another persisted report.

Before implementing the adapter, preserve the recorder's exclusive publication and test exact arguments, selected working directory, deadline partial effects, path presentation, evaluated conditions, output-enforcement limits, publication conflicts, child failure, parse failure, and interrupted recording. These are planned implementation cases; reviewing this specification does not execute them. Unsupported capabilities must remain explicit rather than silently ignored or claimed as enforced.
