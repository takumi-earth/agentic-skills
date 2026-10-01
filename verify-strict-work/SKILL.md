---
name: verify-strict-work
description: "Honor strict verification authority, bans, scope, order, and acceptance claims. Ban-only or commit-only work uses the compact core; load command, matrix, or lifecycle detail only for its authorized mode. No substitute checks or automatic ledgers."
---

# Verify Strict Work

Treat verification as an authorization and acceptance protocol. An invocation does not authorize commands, a ledger, a baseline, broader scope, or substitute evidence.

## Establish authority before commands

Use the current task contract: who owns verification, what is permitted or prohibited, the exact command/scope/order, and the accepted pass criteria. Implementation or a command written in a plan does not grant verification authority. Preserve purpose-bound exceptions without erasing a wider prohibition. Apply already-loaded unchanged instructions rather than rereading them at every gate.

For a ban-only task, enforce the rules below without loading execution, matrix, recovery, or long-run detail. A staged-only `--no-verify` commit follows `$commit-strict-work` and keeps all source inspection inside the authorized index.

## Respect bans semantically

If verification is prohibited or reserved to the user:

- Do not run focused tests, lint, format checks, metadata probes, mutation tools, or cheap gates.
- Do not substitute broad searches, source audits, reachability scans, or manual absence/completeness proofs.
- Do not establish new correctness, cleanliness, reachability, or acceptance claims through prohibited verification.
- Preserve earlier results that still apply to the relevant inputs and scope; a ban does not erase valid existing evidence.
- Report implementation state and the limits of existing evidence; await the user's results where required.

Narrow source inspection needed to implement a known edit is not verification. Inspection intended to prove absence, completeness, or correctness is. Git inspection remains purpose-scoped, and a verification ban does not authorize worktree inspection during a staged-only task.

## Disclose the authorized mode

Before preparing or running an authorized formatter, generator, diagnostic, or acceptance command, load [command-protocol.md](references/command-protocol.md). It owns exact scope and ordering, closed snapshots, whole diagnostic batches, post-format checks, canonical surfaces, unfiltered output, duration limits, and failure handling. Do not preload it for a future command phase or reread it while unchanged and retained.

When designing or adjudicating operation/lifecycle behavior, test execution, or canonical acceptance evidence, load [behavior-evidence.md](references/behavior-evidence.md). It preserves complete typed outcomes and attribution without making every task create a behavior matrix or durable ledger.

## Keep claims precise

Keep planned, written, compiled, executed, assertion outcomes, process exit, canonical gate status, and user acceptance separate. A successful build does not prove a test body ran; exit `0` alone does not prove behavioral or canonical acceptance. Successful inner assertions with a nonzero process status are not a passing gate. A focused success cannot replace the required canonical gate.

Reconcile only claims affected by changed inputs. Classification and attribution do not authorize another inspection, command, historical checkout, audit, or persisted record. Use existing task context or an already-authorized artifact; do not copy verification history into a minimal implementation goal.

Report the actual state, for example `Implementation complete; verification not authorized`, or `Assertions passed; the command exited 1 because the coverage threshold failed`. Never infer a broader state than the authorized evidence supports.
