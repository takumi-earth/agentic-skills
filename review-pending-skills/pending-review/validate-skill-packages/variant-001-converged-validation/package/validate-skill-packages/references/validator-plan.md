# Validator plan

Use `python3 scripts/run_skill_validators.py <plan.json>` when a declared batch needs per-command accounting. A plan contains `schema_version: 1`, a nonempty `packages` string array, and a nonempty `validators` array. Each validator declares a unique `id`, `kind` (`canonical`, `harness`, or `supplemental`), boolean `required`, a nonempty `command` argument array, and optional `interpreter`.

For example, a canonical command is `["skills-ref", "validate", "{package}"]`. A Python helper can declare `command: ["path/to/quick_validate.py", "{package}"]` and `interpreter: "python3"`. Arguments are passed without a shell; `{package}` is substituted in each argument. An argument beginning with `~/` is expanded for execution.

Relative package and command paths use `working_directory` when supplied; otherwise they use the plan directory. A relative `working_directory` is resolved from the plan directory. The directory must exist. Optional `max_output_bytes` defaults to `20000` per reported stream and `timeout_seconds` defaults to `120` per command. Output limits bound the report; subprocess capture still collects output until exit or timeout.

The driver prints progress events on stderr before and after each command, with target, validator, position, and elapsed time. Stdout contains one JSON result. Help and invalid plans do not emit command progress.

Each command result preserves start state, process exit, timeout, `process_passed`, explicit `inner_assertions`, bounded stdout/stderr with byte counts, and duration. UTF-8 decoding replaces invalid bytes for display while retaining original byte counts. The supported assertion convention is a complete line `ASSERTIONS: passed` or `ASSERTIONS: failed`, ignoring case and surrounding whitespace. A failure wins if both occur; other output is `not-reported`.

Overall success requires every required command to start, exit `0`, and avoid explicit assertion failure. Optional failures remain visible. Exit `0` means required checks passed, `1` means a required check failed or was unavailable, and `2` means an invalid plan or unreadable input. Inner assertion results never replace the process exit status.

The driver itself does not install tools or modify packages; declared validators retain their real effects and require caller-owned authority. It never adds a fallback or changes caches or temporary locations. Preserve an intended-command permission failure for the caller's escalation workflow. Normalize home paths in reports and keep transient plans under the resolved canonical repository's `.scratchpad/` unless a user-selected deliverable destination applies.
