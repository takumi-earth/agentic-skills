---
name: orchestrate-codex-forks-and-waits
description: "Budget interruptible Codex subagent waits to avoid context-wasting liveness polls. Use only during explicitly authorized delegation when a worker remains active and the user requests long waits, low-frequency polling, or efficient mailbox handling."
---

# Orchestrate Codex Forks and Waits

Apply the protocol in `references/wait-budget.md` after an authorized worker has started.

## Select the wait ceiling

Read the current `wait_agent` tool metadata. Use the greatest accepted interruptible timeout that satisfies the user's explicit wait instruction and any stricter active harness requirement. Do not replace it with a chain of shorter liveness polls.

## Re-poll only for a reason

Another wait is justified only after:

- the prior wait reached its timeout while the worker remains active;
- a substantive worker update requires another work interval;
- the user explicitly requests status and then asks the work to continue;
- a steering message was reconciled and the worker remains authorized.

Do not poll merely to demonstrate activity. Send the user a concise update before a long wait when needed, then rely on the interruptible mailbox.

## Preserve authority and steering

A wait changes no task authority. New user input interrupts the wait; classify whether it replaces, narrows, or adds to the active request before another worker effect. Use `$reconcile-live-steering` when applicable.

Validate maximum-timeout selection, timeout and re-wait, immediate completion, new user steering, an already idle worker, no delegation authority, and a platform-imposed shorter ceiling.
