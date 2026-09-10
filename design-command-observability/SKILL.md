---
name: design-command-observability
description: "Design progress, decision, and outcome reporting for CLI and workflow commands. Use when a command blocks, fans out, performs multiple phases, makes policy decisions, waits on network or child processes, appears hung, needs elapsed-time reporting, must keep machine-readable stdout exact, or needs an explanation of a guarded no-op or partial failure."
---

# Design Command Observability

Make healthy work, slow work, blocked work, and failed work distinguishable without changing command semantics or contaminating requested payloads.

## Diagnose the missing signal

Separate performance from observability:

- Elapsed time alone does not prove a performance defect when the command performs several legitimate operations.
- Silence during materialization, probing, dependency resolution, child execution, or user input is an observability defect even when the final duration is acceptable.
- A final changed-count summary does not explain which decision was made or where time was spent.

Map the operation graph, including policy decisions, blocking calls, nested workflows, captured probes, user waits, cleanup, and failure short-circuits before adding output.

## Keep identity with the owner

- Domain owners emit typed phase, work, and decision events before the corresponding effect.
- Generic runtime or CLI capabilities own monotonic timing, output routing, and rendering mechanics.
- Adapters render typed events; they must not infer rationale afterward from changed files or child output.
- Nested workflows designate one progress owner. Keep silent supplements silent when an outer command already reports the same work.

Do not wrap runner dispatch blindly or centralize domain vocabulary in a generic logger.

For a failed policy or resolution decision, keep the checked condition, expected and received values, stage, and code with the deciding owner. Carry those facts through the existing typed result or a structured exception; preserve result-based handoffs. At the adapter boundary, distinguish expected policy rejection from unexpected implementation errors without imposing a universal exception hierarchy.

## Emit actionable progress

Before blocking work, report the smallest useful typed facts:

- active command, phase, or semantic operation;
- target identity such as repository, package, tool, document, or provider;
- selected policy branch and its authoritative reason when a decision is being made;
- deterministic item index or count for fan-out work;
- cumulative elapsed time from one command-level monotonic origin;
- explicit wait, retry, no-op, completion, or stop reason.

Preserve failure ordering. Emit an event before the effect it names, never as a post-hoc reconstruction after later mutations.

## Explain guarded outcomes

A successful guarded `no-op` requires a named guard that matched, positive proof that the exact desired state was already present, and zero writes. State the operation, target, checked condition, expected and received values, desired state, and write count. Explain those facts in plain language before using shorthand.

Keep neighboring application outcomes distinct:

- `write`: the guard matched and the operation completed one or more writes;
- `blocked`: a required guard failed, so the dependent write was not attempted;
- `skipped`: the operation was not attempted for the stated reason;
- `failed`: the operation encountered an error; report any observed partial effects and write count rather than implying nothing changed.

Report verification separately as `not-run`, `passed`, or `failed`, with the check's scope and any reason it was deliberately unrun. Keep the application outcome and its actual effects visible after verification. Zero writes alone prove neither guard success nor a passed build, test, or repository gate.

## Preserve output contracts

- Keep requested Markdown, JSON, or text payloads byte-exact on stdout. Send progress to a payload-safe diagnostic stream.
- Keep help, version, completion, and invalid grammar effect- and progress-free unless their public contract says otherwise.
- Preserve existing child stream behavior; do not capture or replay merely to add progress.
- Render one canonical typed impact or decision body across interactive and noninteractive paths when their details must match.
- Avoid a new dependency when injected standard-library timing and output capabilities satisfy the contract.

For hooks, follow the selected schema, envelope, permitted channels, silence rules, and process-exit semantics. Preserve an empty-stderr contract where required. When an authorized workflow uses both stderr and agent-visible context, derive both from the same diagnostic facts; stderr emission alone proves neither visibility nor durable capture. Hook process exit `0` does not establish decision success.

Use the existing response or authorized record. Rendering or classifying a diagnostic does not authorize another audit artifact, diagnostic channel, or persistence workflow.

## Test both visibility and silence

Pin:

- exact event order and identity;
- monotonic cumulative elapsed rendering through injected time;
- event-before-effect and failure short-circuit behavior;
- phase, fan-out, no-op, and blocking-wait polarities;
- matched guards, desired-state proof, actual write counts, partial failure, and separate verification results;
- payload stdout remaining exact;
- help and parse-error silence;
- nested supplement silence and no duplicate owner output.

Do not use real long waits in focused tests. Inject time and operation outcomes.
