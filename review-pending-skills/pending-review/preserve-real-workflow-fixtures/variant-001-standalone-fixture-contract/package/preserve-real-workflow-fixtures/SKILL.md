---
name: preserve-real-workflow-fixtures
description: "Design or review workflow, integration, schema, repository, generated-file, or source-input tests whose behavior depends on real files and semantic artifact roles. Use when a scenario needs a current target, materialized snapshot, manifest, sidecar, source tree, valid source file, or intentionally invalid snippet. Require committed role-specific fixtures and exact-byte loading when file identity is part of the contract. Do not use for a pure value-level parser test whose public input is only an in-memory string."
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

- Use a committed file when production consumes a file, path, source tree, materialized checkout, formatter, linter, compiler, or generator input.
- Load scenario-defining files byte-for-byte. Do not mutate them with replacement, formatting, concatenation, marker substitution, or runtime rendering before seeding the workflow.
- Keep role-specific fixtures distinct even when their current bytes match. A template snapshot does not become a current-target fixture by reuse.
- Name fixtures after their role and distinguishing state. Let an intentional byte-identical pair reveal role coverage rather than hiding it behind one constant.
- Use an inline value only when text or bytes are themselves the complete public API input and no filename, path, tooling, or materialization behavior is under test.

## Treat source as source

- Store valid Rust or other valid program source in a committed file with its real extension.
- Store an intentionally invalid non-compiler snippet as inert fenced code in a non-compiled text or Markdown fixture.
- Keep a compile-fail source file only when full compiler integration is explicitly the behavior under test; do not use that exception for incidental invalid syntax.
- Stop if a source-free scenario unexpectedly appears to require source. Resolve whether the requirement is real before inventing a source string.

## Separate inputs from oracles

- Parse final documents and compare typed models when semantics, not exact bytes, are the contract.
- Compare exact bytes only when byte preservation or rendering is the external behavior.
- Do not generate a golden snapshot from the same inline construction that produced the input; correlated construction is not independent evidence.
- Cover positive behavior and the corresponding rejection or pre-effect guard through real role-correct inputs.

## Keep scope proportional

Apply the contract to new or modified scenarios. Do not migrate unrelated existing fixtures merely because the current file contains older inline data unless the user authorizes that broader scope.

