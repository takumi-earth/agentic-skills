# Interruptible worker waits

Use this reference when explicitly authorized workers are running and the root needs to wait for a reply, decision, dependency, or handoff. Long, interruptible native mailbox waits are the default when no independent required root work is ready. The current harness owns tool names, accepted timeout values, interruption behavior, and returned state.

## Select the permitted wait

Read the live wait-tool contract. Honor the user's selected timeout; otherwise choose a long supported interruptible wait consistent with stricter active requirements. Prefer a deadline measured in minutes when the tool supports it. A fifteen-minute deadline can be appropriate, but neither that example nor a previous harness's maximum is a portable limit. Distinguish an interruptible mailbox wait from a blocking sleep that prevents the root from responding to input.

The timeout is a deadline for the current wait, not a polling interval or a required sleep. Where the live tool supports it, agent messages or new user input end the wait early. Workers communicate concrete blockers, needed decisions, and completed handoffs directly; the root does not need recurring status requests to discover them. Do not divide a permitted long wait into short checks merely to demonstrate activity.

Send a concise user update when a material finding, decision, failure, or barrier changes the task state. Do not send minute-by-minute waiting updates or run routine agent-status, Git, or filesystem checks to fill the wait. Each inspection needs a concrete preservation, integration, handoff, or changed-state purpose. A timeout budget belongs in the existing task context; waiting does not require a new persisted ledger or status audit.

## Handle the returned event

| Event | Interpretation and next action |
|---|---|
| Timeout without an update | Only the deadline elapsed. Use delivered updates and known task state to decide whether to wait again. Do not manufacture a progress update, Git check, or status audit. Consult native status only when a specific unresolved state affects the next decision. |
| Worker update | Consume the message and perform only required, authorized integration. Wait again if work remains pending. An intermediate message does not close an implementation wave or authorize dependent verification. |
| User status question | Answer briefly and resume the authorized work unless the user pauses, cancels, or changes it. No renewed instruction to continue is required. |
| User steering | Use `$reconcile-live-steering` before the parent's next task effect. Interrupt any worker whose continuing effects are no longer authorized; interruption of the parent's wait does not itself stop workers. |
| Idle worker or final handoff | Distinguish successful handoff, failure, and interruption. Idleness or a completion claim alone does not establish the assigned deliverable; apply the existing root integration rules. An interrupted worker may remain available to continue its same authorized slice. |

Waiting changes no authority. Between waits, perform only work already required and authorized by the active request, preserving ownership, wave barriers, verification limits, and stopping conditions.
