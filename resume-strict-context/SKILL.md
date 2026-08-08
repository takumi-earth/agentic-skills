---
name: resume-strict-context
description: "Recover authoritative state for long-running `strict*` ecosystem work after context compaction, rollout continuation, or a copied handoff. Use before any task action when a summary replaces prior context, when the user says context was compacted, or when a resumed session must recover an unfinished living-goal slice."
---

# Resume Strict Context

Treat summaries as navigation evidence. Reconstruct the task from the complete living goal and current authority before reading partial source as intent.

## Stop before task action

- Announce that compaction or continuation occurred.
- Do not edit source, launch verification, start a new research lane, or resume a worker wave yet.
- Preserve the current harness goal status exactly. Compaction never blocks, unblocks, completes, or otherwise changes a goal and never grants authority.

## Reload authority in order

1. Read the current live user message completely.
2. If the active harness supplies an exact living-goal path, use only that path and do not enumerate or select sibling attachments. Treat another attachment as historical input only when the user or active harness explicitly designates it. If no active path exists, resolve the artifact from the latest explicit user designation or current goal metadata; ask if two sources are explicitly active.
3. Read the protected causal section first, then the entire goal from start to end. Continue in bounded chunks until EOF; a truncated read is not a full read.
4. Reload every skill contract required by the unfinished phase.
5. Consult a compaction summary only to locate artifacts, workers, commands, or evidence. Never let it supersede fuller source authority.
6. Inspect source only after the active causal state has been reconstructed.

## Reconstruct the active state

State, from source artifacts:

- objective and concrete completion boundary;
- current phase and exact unfinished owner-level slice;
- protected authority, mutation, barrier, cleanup, and persistence sequence that governs that slice;
- last completed effect and exact next permitted action;
- authorized and prohibited reads, writes, commands, repositories, verification, commits, pushes, and delegation;
- local causal stops, pending user decisions, any currently observed whole-goal impasse, active workers, and the expected next event;
- verification ledger and generated work still outstanding.

Deduplicate copied user messages, forked history, and repeated requirements. Preserve repetition as a priority signal without multiplying work.

## Detect drift

- Compare the summary, goal status, and current source shape.
- If partial source conflicts with protected architecture, treat source as incomplete or drifted implementation, not new authority.
- If mutable status in the goal is stale, reconcile it before source edits without rewriting the protected target.
- If the full chain cannot be reconstructed uniquely, stop effects that depend on the ambiguity and repair the living contract or request the missing decision. Continue causally independent authorized work when it remains; use `$maintain-living-goal` and the harness audit rather than pre-deciding a whole-goal `blocked` transition.

## Resume the same slice

- Restate the active causal chain and unfinished step in concise commentary.
- Continue the interrupted slice; do not restart completed research or choose a more convenient issue.
- Use `$reconcile-live-steering` if the current message adds, overrides, or duplicates the carried-forward contract.
- Use `$maintain-living-goal` for the next pre-edit reconciliation and pruning pass.

Do not present memory-derived or summary-derived state as confirmed current when the authoritative file has not been reread.
