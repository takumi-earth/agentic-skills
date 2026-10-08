---
name: codex-peer-collaboration
description: "Develop and maintain runtime-owned peer collaboration between existing independent Codex sessions on Mac and Ubuntu, including source-built app-server integration with desktop, TUI, and phone clients. Use when investigating, planning, implementing, or resuming this integration; ordinary subagent orchestration is a separate workflow."
---

# Codex Peer Collaboration

Continue the shared-fork integration from its durable record. Preserve the user's chosen runtime ownership and distinguish verified source behavior from client behavior that still needs evidence.

## Working record

- Read [the living plan](references/plan.md) before starting or resuming this project. Reuse a complete unchanged reference already retained in context; a new symbol, status question, or continuation does not require another read.
- Read [the runtime investigation](references/runtime-investigation.md) when tracing package selection, daemon lifecycle, desktop attachment, transport, or message authority. Use its semantic owners and unresolved questions instead of repeating discovery.
- Read [the upstream maintenance strategy](references/upstream-maintenance.md) when designing integration points, carrying the feature to a newer Codex release, or reducing recurring upgrade effort. Its automation design is a proposal, not an implemented updater.
- Keep user decisions, verified facts, hypotheses, and proposed work distinct. A historical process snapshot or source locator is evidence at its recorded checkpoint, not proof of current state.
- Update the existing plan after material user steering, implementation progress, source changes, or external-state changes. Preserve settled decisions and refresh only the affected evidence. Do not create competing plans or new audit versions to restate unchanged findings.
- A plan records authority; it does not grant additional implementation, verification, installation, restart, activation, delegation, or Git authority. An exact active goal supplied by the harness keeps its separate lifecycle authority.

## Runtime ownership

- Implement peer collaboration in the shared Codex fork, owned by the app-server runtime and available through its tool pipeline. Desktop, TUI, and phone clients consume that capability.
- Keep the peer registry, policy, delivery state, and connection lifetime independent of a TUI-owned listener. An internal transport adapter does not transfer ownership to a separately configured peer service.
- Use a focused component and thin integration with existing session and tool services. Preserve the repository's crate ownership guidance instead of growing central modules merely because they are convenient.
- Keep peer operations distinct from the existing subagent-tree API. A running child remains a child. Peer assignments target existing independent sessions and retain the recipient's user-selected task and constraints.
- Preserve explicit-user-request requirements for spawning, creating, or forking sessions. Apply the user's standing permission to existing-peer discovery, communication, replies, and bounded delegation within its actual scope.
- Derive sender identity from runtime context and authenticated host identity. Preserve peer messages as attributed tool-originated context; do not turn them into new human instructions or silently override recipient settings.

## Source and client integration

- Use the user-selected Codex checkout. The plan records the checkout verified in this session; do not substitute a similarly named fork.
- Trace executable/package selection, helper resolution, daemon discovery, and transport in source. A desktop UI selector is not a prerequisite for this investigation.
- Keep these claims separate: a package is valid, a daemon selects it, a client attaches to it, and the model receives its peer tools. Prove each required handoff before claiming the desktop uses the fork.
- Distinguish an MCP child's `CODEX_CLI_PATH`, a plugin marketplace source, and the desktop's actual backend executable. Their names do not establish the same owner.
- Build matching platform packages from the shared source revision and verify the running app-server and `codex-code-mode-host` provenance. Preserve app-provided integration resources at their actual owner.
- Scope cross-host discovery to enrolled hosts and relevant existing sessions. Qualify targets with host and thread identity; define bounded reads, delivery receipts, reconnect behavior, and duplicate protection.

## Work and handoff

- Follow the phase the user requested and continue authorized work without reopening settled ownership. Runtime activation is a separate effect from writing a plan or building a package.
- When a patch upgrade or retention workflow is authorized, use `$upgrade-codex-patch` for its exact build, audit, retention, and publication contract. This skill does not expand that workflow's command surface.
- That workflow's authorized default `just i` installation includes native daemon selection and its managed restart. Preserve that authority while following its installation reference for command lifetime, shared-feature compatibility, and recovery; do not add a second approval for the same package-selection effect. Changes to shared feature policy keep their own authority.
- Before ending a substantive phase, record changed facts, concrete artifacts, validation actually performed, remaining uncertainty, and the next unfinished action in the plan.
- Report source inspection, structural skill validation, compilation, executed behavioral evidence, and end-to-end client verification separately.
- Qualify tool-availability claims by host, client, and turn. An automatically recovered turn and a later normal TUI turn can expose different inventories. Separate observed absence, live endpoint failure, source behavior, and inferred recovery ordering; refresh the affected current status when tools return. Preserve the selected runtime-owned architecture while recording the TUI bridge's actual behavior.
