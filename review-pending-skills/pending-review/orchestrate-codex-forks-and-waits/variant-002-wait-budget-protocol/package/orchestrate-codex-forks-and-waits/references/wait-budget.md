# Wait-budget protocol

Use this reference only after explicit user authority has started a Codex subagent.

## States

| State | Condition | Next action |
|---|---|---|
| `worker-active` | The worker is running and no new message needs handling. | Call `wait_agent` once with the greatest supported interruptible timeout allowed by current instructions. |
| `timeout` | The wait returned only because its timeout elapsed. | Confirm the worker is still active from the wait result, then wait again at the same ceiling. |
| `worker-update` | A substantive message or final handoff arrived. | Consume it, integrate any required work, and wait again only if the worker remains active. |
| `user-steering` | New user input interrupted the wait. | Reconcile the steering before any further worker effect. |
| `worker-idle` | The worker finished, failed, or was interrupted. | Stop waiting and handle the terminal result. |

## Timeout selection

The Codex collaboration tool currently documents a maximum `wait_agent` timeout of `3,600,000` milliseconds. Treat live tool metadata as authoritative if it differs. Choose that maximum when the user asks for the longest waits, unless an active harness rule requires a lower exact ceiling.

Do not divide one permitted long wait into periodic status polls. The mailbox wait is interruptible by agent updates and new user input; use that mechanism instead of consuming conversation context.

## Non-lanes

Waiting does not authorize repository inspection, optional preparation, another worker, expanded history, or a status audit. Between waits, do only work already required and authorized by the active request.
