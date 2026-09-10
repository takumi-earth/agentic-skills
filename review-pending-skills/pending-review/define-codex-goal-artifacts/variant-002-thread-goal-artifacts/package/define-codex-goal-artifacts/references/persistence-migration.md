# Persistence, replacement, and source migration

This is a concrete proposed migration for the durable variant. It is inert and does not authorize changing a database, source checkout, active goal, or hook.

## State and transaction contract

Use the existing `thread_goals` row and `goal_id`. Add `objective_revision INTEGER NOT NULL DEFAULT 1` with a positive-integer constraint and `objective_artifacts_json TEXT NULL`. SQL `NULL` represents a legacy association that was never recorded; a non-NULL value must decode as the strict `GoalArtifactSetV1` object in `thread-goal-artifact-schema.md`. JSON `null` is invalid. Do not backfill associations by searching objective prose or attachment directories.

The internal goal model carries an optional artifact set and the objective revision. Native protocol/tool projections expose the set with its goal identity; do not rely on timestamps, title equality, or thread identity alone. Validate the complete proposed row before admission, then update objective, revision, and artifact set in the same transaction, guarded by the expected goal ID and objective revision. Return the committed snapshot. Failure preserves the prior association and reports the failed condition; it does not partially replace metadata.

An artifact update is an explicit internal operation: `Keep`, `Replace(GoalArtifactSetV1)`, or `Clear`. `Clear` records a known no-file selection for the new/current revision; it does not mean SQL `NULL`. `Replace` validates the designation and all referenced identities. `Keep` is valid only when the objective bytes are unchanged. Legacy absence may remain absent during status/accounting operations.

| Operation | Binding behavior |
| --- | --- |
| Create a new goal or replace a completed goal | Use the newly allocated goal ID, revision `1`, and a newly verified artifact set, `none`, or `unavailable`. Never inherit the previous goal's current artifact. |
| Status-only pause, resume, block, completion, budget, or accounting update | Preserve goal ID, objective revision, and association. File availability is a separate current observation. Existing status authority remains unchanged. |
| Edit objective text on the same goal | Increment the revision and replace or clear the association explicitly. Reject an implicit `Keep`; matching an older objective hash is insufficient. Preserve unrelated accounting and creation state. |
| Replace an entire goal snapshot | Restore only the association bound to that snapshot's goal ID/revision/objective hash, through the already authorized snapshot operation. An older snapshot cannot silently supersede the current one. |
| Delete a goal record | Remove its stored association under existing record-deletion authority; leave referenced files untouched. |
| Same-runtime resume | Read the stored set and verify current binding/availability. No earlier tool response is needed. |
| Fork to a new thread | The trusted fork operation establishes a new thread/goal binding. Carry a selected association only when the authorized fork contract explicitly carries that goal designation; otherwise retain descriptors as historical inputs and mark selection unavailable. A fork does not itself authorize writes to a shared goal file. |
| Move across machines or stores | Keep artifact identity and selection evidence; require an explicit trusted storage/namespace mapping before resolution. Missing files and absent mappings remain unresolved. |

For same-goal objective edits, `objectiveRevision` changes even if the selected pathname is deliberately retained. The producer must rebind that selection to the new revision through the existing user designation; it need not ask again merely because a status changed. A new decision is needed only when the controlling designation is actually ambiguous or changes.

Migration must preserve old rows and the distinction between SQL absence and known no-file selection. Metadata-aware writers preserve the new columns through every insert, update, snapshot replacement, and return projection. Old writers that can replace rows while dropping the columns are incompatible with this profile; do not enable mixed writers without a preservation adapter. An unknown future metadata version is preserved inertly or rejected at the selected compatibility boundary, never silently reset to legacy absence.

## Revision-attributed integration map

These files were read through EOF with no working-tree differences at `~/rust-forks/codex-orig`, revision `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`:

| Source and symbol | Observed behavior and proposed integration |
| --- | --- |
| `codex-rs/state/src/model/thread_goal.rs`: `ThreadGoal`, `ThreadGoalRow`, `try_from_row` | Owns the internal goal ID, objective, status, accounting fields, and row conversion. Add revision and optional association to both the model and conversion. |
| `codex-rs/state/src/runtime/goals.rs`: `GoalUpdate`, `insert_thread_goal`, `replace_thread_goal`, `replace_thread_goal_snapshot`, `update_thread_goal` | Allocates new goal IDs for replacement, preserves an ID for objective edits, and maintains SQL projections. Add atomic artifact/revision operations across these paths; the existing ID alone does not identify an objective revision. |
| `codex-rs/ext/goal/src/tool.rs`: `handle_create`, `handle_update`, `protocol_goal_from_state`, `GoalToolResponse` | Builds tool responses from state. The current projection omits the internal goal ID and all artifact metadata; update the chosen protocol projection losslessly. `update_goal` is status-only here. |
| `codex-rs/hooks/src/events/post_tool_use.rs`: `command_input_json` | Copies the structured `tool_response`. Preserve the adopted response's metadata through this boundary. |

The state runtime's inline tests include goal replacement, stale goal-ID rejection, objective edits preserving usage, and concurrent partial updates. They were read, not executed as part of this specification correction. A future implementation must extend behavior tests for atomic objective/association changes, legacy rows, status preservation, fork binding, and deleted artifacts under its authorized command matrix.

The current Python owner at `~/agentic-skills`, revision `c761c38`, is `maintain-living-goal/scripts/goal_artifact_resolution.py`; both `goal_completion_handoff_hook.py` and `auto-skill-enhancer/scripts/post_goal_review_hook.py` consume it. All three files were read completely. Keep typed selection in the shared resolver and hook presentation in its adapters. Existing legacy resolution is not proof of this proposed durable protocol.

Source revision and file inspection establish these integration locations, not the running binary, a completed database migration, or a tested protocol. Selecting this alternative for implementation and enabling its producer remain separate user decisions.
