---
name: preserve-real-workflow-fixtures
description: "Design or review workflow, integration, schema, repository, generated-file, or source-input tests whose behavior depends on real files and semantic artifact roles. Use when a scenario needs a current target, materialized snapshot, manifest, sidecar, source tree, valid source file, or intentionally invalid snippet. Preserve role identity and the scenario's explicit committed-file or exact-byte requirements. Do not use for a pure value-level parser test whose public input is only an in-memory string."
---

# Preserve Real Workflow Fixtures

Make the fixture observe the same artifact role that production consumes.

## Classify every scenario input

Before writing test setup, name each input as one of:

- current target;
- materialized template or generated snapshot;
- expected generated result;
- manifest, sidecar, policy, or configuration file;
- valid source file or source tree;
- intentionally invalid snippet;
- process or service outcome;
- semantic assertion oracle.

Read [the fixture-role contract](references/fixture-role-contract.md) when a scenario contains more than one file role, source code, or a neighboring fixture that appears reusable.

## Preserve the production boundary

- Reproduce the file, path, source tree, tooling, or materialization boundary that the scenario actually exercises. A file-consuming API alone does not require committed fixtures or prohibit runtime construction.
- Honor an explicit requirement for dedicated committed files or unchanged starting bytes. When exact initial bytes are contractual, load them without replacement, formatting, concatenation, marker substitution, or runtime rendering.
- Keep roles and identities distinct when the scenario relies on that distinction, even when bytes match. A template snapshot does not become a current target merely because it shares content. Routine fixture reuse remains valid when it preserves the scenario contract.
- Name fixtures after their role and distinguishing state. Let an intentional byte-identical pair reveal role coverage rather than hiding it behind one constant.
- Permit small parser strings, tokens, IR, temporary crates, and controlled fixture mutation when they faithfully establish the selected scenario. Materialize files before invoking a boundary that consumes files; runtime construction must not replace explicitly required starting artifacts.

## Treat source as source

- Give tool-consumed source the path and extension required by the toolchain. Preserve committed source files when the scenario requires them; parser data may remain a small string or structured value.
- Keep intentionally invalid parser data outside unrelated compilation or lint discovery, using inline data or an inert fixture as appropriate.
- Preserve compile-fail files when compiler behavior is the contract; they are distinct from incidental malformed parser inputs.
- Stop if a source-free scenario unexpectedly appears to require source. Resolve whether the requirement is real before inventing a source string.

## Separate inputs from oracles

- Parse final documents and compare typed models when semantics, not exact bytes, are the contract.
- Compare exact bytes only when byte preservation or rendering is the external behavior.
- Do not generate a golden snapshot from the same inline construction that produced the input; correlated construction is not independent evidence.
- Cover positive behavior and any reachable rejection or protected-effect guard required by the testing contract, using role-correct inputs.

## Keep scope proportional

Apply the contract to new or modified scenarios. Do not migrate unrelated existing fixtures merely because the current file contains older inline data unless the user authorizes that broader scope.

During planning, settle load-bearing artifact roles and identity requirements. Routine fixture filenames can be selected during implementation when they do not alter those decisions.
