---
name: classify-test-evidence-state
description: "Classify test and verification evidence without conflating written source, compilation, execution, passing assertions, process status, focused scope, and canonical acceptance. Use when tests are written under a verification ban, worker summaries claim coverage, ledgers close rows, or inner assertions and command exit status differ."
---

# Classify Test Evidence State

Name exactly what happened and what remains unproven.

## Use the evidence lattice

Read [the evidence-state model](references/evidence-state-model.md). Record each artifact or gate as one or more monotonic observations:

- `declared` or planned;
- `written` but unexecuted implementation;
- `compiled` in a named configuration;
- `executed` in a named scope;
- `assertions-passed` or failed;
- `process-passed` with exit `0` or nonzero;
- `focused-gate-passed`;
- `canonical-gate-passed`.

Do not infer a later state from an earlier one. A file containing assertions is not behavioral evidence. Passing assertions inside a process that exits nonzero are not a passing command. A focused pass is not an unrun canonical gate.

## Preserve authority

This classification never authorizes a test command. Under a verification ban, record `written` and stop; do not route around the ban with scans or manual proof. Treat worker and agent verdicts as leads until the underlying authorized evidence is available.

## Use precise completion language

State the exact scope and missing transition, such as `implementation written; execution not authorized`, `assertions passed; process failed`, or `focused gate passed; canonical gate not run`. Close a behavior ledger only from evidence that observes the claimed owner and contract.
