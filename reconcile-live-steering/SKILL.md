---
name: reconcile-live-steering
description: "Classify and reconcile user messages that arrive while Codex is actively working. Use when a user interrupts tool work, adds or overrides a requirement, supplies diagnostics, changes authorization or priority, asks for status, corrects external state, or repeats carried-forward context after compaction."
---

# Reconcile Live Steering

Treat a mid-work user message as a task-state event. Preserve its exact wording, decide how it changes the active contract, and invalidate only the work it actually supersedes.

## Freeze the next effect

Before another write, process launch, worker wave, verification command, commit, or external action:

- Read the complete live message rather than reacting to one keyword.
- Preserve the current operation state and any already-produced evidence.
- Stop or interrupt active work only when the message overrides it, explicitly asks to stop, or continuing would create unauthorized effects.
- Answer a status question, then continue only if the underlying request remains active.

## Classify the message

Choose the narrowest supported class:

- **Override or cancellation:** Drop invalidated queued work and follow the new priority. Do not finish one last check or preserve a formerly valid restriction after explicit supersession.
- **Additive requirement:** Merge it into the unfinished request and retain every compatible earlier obligation. Preserve user-specified order when successive messages extend a sequence.
- **Clarification:** Replace the ambiguous interpretation, not the whole objective. Correct affected plans and assumptions before continuing.
- **Diagnostic evidence:** Record the complete batch and structural owner. Do not infer a new product requirement, blame, or permission merely from an error log.
- **Acceptance or monitoring instruction:** Record the exact gate state, wait/continue request, or stop condition. A green report does not expand commit or publication authority.
- **External-state or user self-correction:** Reclassify the evidence without rewriting product policy to compensate for a host or tooling defect.
- **Duplicate or copy-forward context:** Deduplicate it semantically. Use repetition to confirm priority, not to create duplicate tasks, effects, or goal entries.
- **Authorization change:** Record the exact action, target, purpose, duration, and whether it supersedes or only narrows an earlier rule.

If evidence supports more than one class, state the combination. Do not classify every correction as a prior violation; distinguish initial constraints, evolving requirements, and confirmed deviations.

## Reconcile authority

Use this precedence unless the user explicitly changes it:

1. Current explicit user decision for the named purpose.
2. Protected user-selected architecture in the living goal.
3. Accepted behavior contracts and tests.
4. Mutable implementation status.
5. Naming, convenience, and optimization preferences.

A later purpose-bound exception does not erase a broader prohibition outside that purpose. A formerly valid scope boundary must not survive after the user explicitly supersedes it.

Update the active plan or living goal before source edits when the message changes target behavior, ownership, phase order, verification, or authorization. Keep incidental diagnostics out of durable target-state text.

## Resume deliberately

- State what changed, what remains active, and what work was discarded or retained.
- Resolve the entire supplied diagnostic batch before rerunning its gate when that policy is active.
- Continue from the unfinished owner-level slice rather than starting a parallel interpretation.
- Keep the goal blocked when the new message requests review or leaves a material architecture decision unresolved.

Do not praise the correction or merely defer. Lead with the concrete contract change and the evidence that determines the next action.
