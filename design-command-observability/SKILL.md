---
name: design-command-observability
description: "Design progress and decision observability for CLI and workflow commands. Use when a command blocks, fans out, performs multiple phases, makes policy decisions, waits on network or child processes, appears hung, needs elapsed-time reporting, or must keep Markdown, JSON, or other machine-readable stdout exact."
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

## Emit actionable progress

Before blocking work, report the smallest useful typed facts:

- active command, phase, or semantic operation;
- target identity such as repository, package, tool, document, or provider;
- selected policy branch and its authoritative reason when a decision is being made;
- deterministic item index or count for fan-out work;
- cumulative elapsed time from one command-level monotonic origin;
- explicit wait, retry, no-op, completion, or stop reason.

Preserve failure ordering. Emit an event before the effect it names, never as a post-hoc reconstruction after later mutations.

## Preserve output contracts

- Keep requested Markdown, JSON, or text payloads byte-exact on stdout. Send progress to a payload-safe diagnostic stream.
- Keep help, version, completion, and invalid grammar effect- and progress-free unless their public contract says otherwise.
- Preserve existing child stream behavior; do not capture or replay merely to add progress.
- Render one canonical typed impact or decision body across interactive and noninteractive paths when their details must match.
- Avoid a new dependency when injected standard-library timing and output capabilities satisfy the contract.

## Test both visibility and silence

Pin:

- exact event order and identity;
- monotonic cumulative elapsed rendering through injected time;
- event-before-effect and failure short-circuit behavior;
- phase, fan-out, no-op, and blocking-wait polarities;
- payload stdout remaining exact;
- help and parse-error silence;
- nested supplement silence and no duplicate owner output.

Do not use real long waits in focused tests. Inject time and operation outcomes.
