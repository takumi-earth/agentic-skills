# Packet and result contract

Run `python3 scripts/build_prompt_matrix.py build <matrix.json> <packet-directory>` to create inert evaluation packets. Use a new output directory under the resolved canonical repository's `.scratchpad/` unless the user explicitly selected another deliverable destination.

The matrix has `schema_version: 1`, a `skill` object containing nonempty `name` and `package` strings and a 64-digit hexadecimal `sha256`, and a nonempty `cases` array. Each case contains:

- `id`: unique lowercase hyphen-case evaluator identity;
- `kind`: `explicit`, `implicit-positive`, `nearest-negative`, `mixed-owner`, `unauthorized-effect`, or `failure-polarity`;
- `prompt`: nonempty natural task text;
- `artifacts` and `allowed_effects`: arrays of nonempty strings;
- `expectation`: evaluator-only `activation` and `execution` verdicts using the enums in the isolated evaluation procedure.

Worker files live in `workers/` with deterministic opaque identifiers. They include the opaque `case_id`, available skill locator, prompt, declared artifacts and effects, and `context_requirement: "fresh"`. They contain neither the evaluator identity nor `kind` or `expectation`. Treat the skill locator as discovery input, not an instruction to activate the skill.

The evaluator-only `manifest.json` maps original case identities to packet files and hashes and records `matrix_sha256`. Never expose it or the source matrix to a worker. Hashes describe the emitted bytes after home-path normalization. Existing nonempty output is refused; an I/O failure is reported as incomplete generation, not success.

After authorized evaluations, collect `results.json` with `schema_version: 1`, the manifest's `matrix_sha256`, and a `results` array. Each result contains the original evaluator `case_id`, `model` including its version or exact identifier, `context_mode: "fresh"`, `activation`, `execution`, `effects`, `output_locator`, `contamination: false`, and `evaluator_rationale`.

Run `python3 scripts/build_prompt_matrix.py validate <matrix.json> <results.json>`. Require one result per case, the same matrix digest, fresh context, valid verdicts, declared effects only, and explicit raw-output and rationale locators. The validator checks the ledger, not the existence or truth of externally referenced evidence; inspect that evidence before accepting a judgment.

Exit `0` means the ledger is valid and its observations match expectations. Exit `1` means a valid ledger records differing observations. Exit `2` means invalid input, invalid evidence structure, contamination, unauthorized effects, or an I/O failure. JSON reports `ledger_valid` separately from `matched_expectation`; no outcome launches an evaluator or authorizes another effect.
