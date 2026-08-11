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

## Load instruction files without aggregate truncation

Build the exact list of trigger-matched `SKILL.md` files and directly required resources before reading their bodies. Do not load unrelated skills merely because they may be useful later.

When more than one instruction file is required:

1. Preflight the entire selected set together. Run one `python3 scripts/plan_instruction_reads.py <path>...` invocation from this package, or use parallel metadata-only calls when a different preflight tool is appropriate. Batch or aggregate existence, logical line counts, byte counts, hashes, and range plans because they contain no instruction bodies. Do not serialize one `wc`, hash, or planner command per file.
2. Read exactly one planned file range in each tool result. Never concatenate files, print several bodies from one command, or combine parallel reads into one orchestration result; aggregate output limits can truncate the composed result even when each nested call has a larger limit.
3. Maintain a small ledger containing `path`, `sha256`, `final_line`, `next_line`, and `complete`. Advance `next_line` only through visibly complete output, and mark a file complete only when the final planned range reaches `final_line` without truncation.
4. If a result is truncated, preserve every earlier confirmed range and resume that file at the first unread line. Do not restart the file or reread complete siblings from the attempted batch.
5. Re-run the planner after all reads when the files may have changed concurrently. If a hash changed, discard only that file's stale ledger entry and read its new plan; do not invalidate unchanged files.

The planner counts an unterminated final line correctly and flags a single line whose bytes exceed the chosen chunk limit. For an oversized line, read that line alone with a sufficiently bounded one-file result; never hide it inside a larger aggregate. Apply the same protocol to directly referenced skill instructions.

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
