---
name: pin-active-goal-artifact-role
description: "Pin the exact harness-designated active goal before answering plan status, completion, or pending-work questions. Use after context compaction or whenever an active goal coexists with historical goals, sibling attachments, ledgers, or generated companions and source attribution could drift."
---

# Pin Active Goal Artifact Role

Keep artifact identity separate from artifact content. Treat the exact path designated by the active harness or current user instruction as the only active goal; never select a sibling because it appears newer, broader, or more detailed.

## Record the role checkpoint

Before a status answer, record internally:

- `active`: the one exact designated goal path;
- `historical`: a path explicitly referenced for provenance only;
- `evidence`: a read-only ledger, report, or frozen snapshot;
- `output`: an artifact the current task is authorized to create or edit.

Do not enumerate attachment siblings to populate this table. Do not infer that a referenced historical goal is active.

## Source current status

1. Read the exact active goal through EOF.
2. Reconstruct its protected decisions and mutable status separately.
3. Use historical and evidence artifacts only for claims the active goal explicitly delegates to them.
4. Map each pending or completed claim back to the active goal and current authoritative state.
5. If two artifacts are explicitly designated as active, stop for the user's choice before editing or reporting either as controlling.

Never let a broader historical product goal supply pending work for a narrower remediation goal. Never treat a role label as authority to read, edit, execute, or mark completion.

## Check both polarities

- Accept a historical link as provenance while keeping current status anchored to the active goal.
- Reject a status answer derived from a sibling, a conversationally older path, or a generated companion that was not designated active.
- Preserve the active path across compaction; a summary is navigation evidence, not replacement authority.
