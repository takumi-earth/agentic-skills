---
name: preserve-real-workflow-fixtures
description: "Route real-fixture decisions through strict-work planning and implementation owners. Use during `strict*` planning or implementation when a test scenario consumes a repository target, template snapshot, sidecar, manifest, generated file, source file, or source tree. Make the active phase owner declare and enforce role-specific committed fixtures without creating a parallel test workflow. Do not use for unrelated existing fixture cleanup or pure in-memory value tests."
---

# Preserve Real Workflow Fixtures

Keep fixture ownership inside the active strict-work phase while preserving one shared contract.

## Route by phase

- During planning, use `$plan-strict-work` and decide every scenario-defining artifact role, filename, exact loading rule, prohibited construction, and semantic oracle.
- During implementation, use `$implement-strict-work` and enforce the selected fixture contract for every new or modified scenario input.
- When replacing a real current target or snapshot with constructed data would change the observed causal boundary, use `$protect-causal-architecture` before changing that evidence edge.
- When verification is authorized, use `$verify-strict-work`; fixture inspection does not prove a gate passed.

Read [the strict owner integration](references/strict-fixture-owner-integration.md) before finalizing a plan or editing test setup that contains more than one file role.

## Preserve the shared invariant

- Represent file-consuming production boundaries with committed, role-specific fixture files.
- Load scenario-defining bytes without runtime construction or substitution.
- Keep current-target, materialized-snapshot, generated-result, and source roles distinct even when bytes match.
- Store valid program source as valid source files. Keep intentionally invalid non-compiler snippets inert and fenced.
- Use parsed or typed assertions when semantics are the contract; exact text is an oracle only when text or bytes are externally observable behavior.
- Stop rather than invent source when the accepted plan declares a scenario source-free.

## Avoid scope drift

This skill records a shared fixture invariant; it does not authorize test edits, formatting, verification, staging, commits, promotion, or repository-wide fixture migration. Preserve unrelated existing inputs unless the user expands scope.

