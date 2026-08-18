---
name: orchestrate-codex-forks-and-waits
description: "Translate an explicitly authorized delegation workflow from stale or foreign harness language into Codex subagent controls. Use when the user names agents or orchestration and also specifies history inheritance, context isolation, or low-frequency long-wait behavior."
---

# Orchestrate Codex Forks and Waits

Use only after the user explicitly requests subagents, agents, delegation, orchestration, waves, parallel work, or a fork. Never infer delegation authority from task size.

## Translate intent, not commands

1. Extract the requested objective, ownership, forbidden paths, allowed effects, stop conditions, model constraints, context policy, and wait policy.
2. Ignore foreign-harness command names and map only their semantics to current Codex collaboration tools.
3. If the user explicitly rejects full history, choose `fork_turns="none"` or the smallest sufficient positive turn count and make the assignment packet fully self-contained.
4. Do not set model or reasoning overrides unless the user or applicable guidance requests them.
5. Preserve every repository and user authority boundary in the worker packet.

## Build a complete assignment

Include objective, protected decisions, owned and forbidden paths, concurrent-work rules, allowed commands and external effects, validation scope, stop conditions, and final handoff evidence. Inherited context never replaces this packet.

## Wait through the mailbox

After a worker starts, use the longest supported interruptible wait consistent with the user's instruction and current harness rules. New user steering may interrupt the wait. Do not spend context on liveness polls; poll again only after a timeout, substantive update, or explicit status request.

Translate an old prompt without reconstructing its full history unless the user asks. Never spawn another worker merely to validate this adapter without separate delegation authority.

## Validate scenarios

Cover explicit full history, explicit no full history, no delegation authority, foreign command names with clear semantics, an underspecified assignment, a long active worker, new user steering during a wait, and worker completion.
