# Interruptible worker waits

Use this reference after explicitly authorized workers have started, when long interruptible waits or restrained polling matter to the task. The current harness owns tool names, accepted timeout values, interruption behavior, and returned state.

## Select the permitted wait

Read the live wait-tool contract. Choose the longest supported interruptible wait consistent with the user's preference and all stricter active requirements, including any blocking-duration or communication limit. Do not preserve a numerical maximum from an older harness or divide a permitted long wait into repeated checks merely to demonstrate activity.

Send a concise progress update before waiting when needed. A timeout budget belongs in the existing task context; waiting does not require a new persisted ledger or status audit.

## Handle the returned event

| Event | Interpretation and next action |
|---|---|
| Timeout without an update | Only the deadline elapsed. Use delivered updates and known task state to decide whether to wait again. Do not claim the wait result confirms current worker status unless the tool actually returns it; consult native status only when unresolved state affects the next decision. |
| Worker update | Consume the message and perform only required, authorized integration. Wait again if work remains pending. An intermediate message does not close an implementation wave or authorize dependent verification. |
| User status question | Answer briefly and resume the authorized work unless the user pauses, cancels, or changes it. No renewed instruction to continue is required. |
| User steering | Use `$reconcile-live-steering` before the parent's next task effect. Interrupt any worker whose continuing effects are no longer authorized; interruption of the parent's wait does not itself stop workers. |
| Idle worker or final handoff | Distinguish successful handoff, failure, and interruption. Idleness or a completion claim alone does not establish the assigned deliverable; apply the existing root integration rules. An interrupted worker may remain available to continue its same authorized slice. |

Waiting changes no authority. Between waits, perform only work already required and authorized by the active request, preserving ownership, wave barriers, verification limits, and stopping conditions.
