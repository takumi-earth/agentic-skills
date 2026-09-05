# Workflow Fixtures

Load this reference when test setup depends on scenario-defining artifact roles, a file or materialization boundary, or an explicit fixture contract. The scenario determines which properties setup must preserve; filesystem access alone does not require committed, immutable fixtures.

## Settle the scenario contract

Identify the current target, materialized snapshot, generated result, manifest or sidecar, source tree, process outcome, and assertion oracle only where those roles affect the scenario. Preserve the production loader and any load-bearing path identity, extension, layout, tooling, or materialization step.

During planning, settle those roles and identity requirements, explicit file and byte obligations, source-free constraints, prohibited substitutes, and the independent oracle. Specify fixture paths when they carry that contract; routine filenames can remain implementation choices. Keep these decisions in the existing task contract.

## Choose inputs by their role

- Preserve an explicit requirement for dedicated committed fixtures and unchanged starting bytes. Load those bytes without replacement, formatting, concatenation, marker expansion, or runtime rendering before the workflow begins.
- Keep current-target and materialized-snapshot inputs independently identifiable when the scenario depends on that distinction. Two committed files with identical bytes are valid when the contract requires separate role-specific files; byte deduplication must not erase that handoff.
- Otherwise, use the construction strategy that exercises the production boundary: role-correct files or trees for filesystem behavior, and parser data, tokens, IR, snapshots, or temporary crates when those test the contract more narrowly. Small parser strings and controlled fixture mutation remain valid where no explicit starting-byte or identity requirement forbids them. `$test-adaptive-source-transforms` owns adaptive workspace variation and its typed oracles.
- Keep source-free scenarios source-free. If a helper appears to require invented source, resolve that mismatch at the helper or scenario contract before seeding the test.
- When tooling consumes valid source files, preserve the relevant extension and source validity. Intentionally invalid parser data may remain an in-memory value; if stored as a file outside compiler integration, keep it inert rather than accidentally compiling or linting it as valid source.
- Use checked-in compile-fail source only for the full compiler-integration behavior allowed by `$implement-strict-work`. Remove incidental invalid or non-idiomatic syntax that is unnecessary for the diagnostic.

## Preserve independent evidence

For a file-consuming workflow, keep the relevant chain observable: `role-correct input -> production loader -> prepared or executed workflow -> typed outcome`. A convenient helper must not bypass the path, parsing, role, or materialization behavior the scenario claims to exercise.

Assert parsed models or typed outcomes when semantics are the contract. Exact bytes are appropriate for a documented rendering or byte-preservation contract, including proof that a rejecting operation made zero edits. A golden result produced by the same construction as the input is not independent evidence.

Preserve the touched scenario's positive behavior and reachable rejection or protected-effect guards. Do not invent a failure or a new public test seam solely to complete a pair.

Apply this guidance to new or modified scenarios within the authorized scope. It grants no unrelated fixture migration, execution, verification, or persistence authority; fixture inspection alone does not establish that a workflow or gate ran.
