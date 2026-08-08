---
name: active-goal-turn-audit
description: "Design and validate a one-pass Codex turn-ending audit for threads whose harness goal remains active. Use when a `Stop` hook should challenge premature stopping, continue independent authorized work, preserve user-owned completion, and avoid counting a same-turn retry as another goal turn."
---

# Active Goal Turn Audit

Create an inert, schema-exact turn-ending adapter that requests one additional audit sample only while the thread's authoritative goal status is `active`. Keep artifact creation separate from hook registration.

## Resolve active status authoritatively

- Use the hook input's `session_id` to query the harness goal store read-only. Do not infer active status from the last assistant message or parse the transcript for a guessed goal state.
- Use a parameterized query and fail open with `{}` when the database, schema, row, or status is missing or unreadable.
- Require the actual `Stop` event, nonempty `session_id` and `turn_id`, and exact boolean `stop_hook_active: false` before reading status.

## Request exactly one same-turn audit

For the first `Stop` pass of an active goal, emit only:

```json
{"decision":"block","reason":"<audit prompt>"}
```

The reason must direct the agent to re-read the full objective and authoritative state, continue every causally independent authorized lane, reject local-review-as-whole-goal-blocker reasoning, avoid inventing work or blocker turns, and leave a candidate completion audit active for explicit user review.

On the recursive pass where `stop_hook_active` is true, emit `{}`. State explicitly that the retry keeps the same `turn_id` and is not another turn in a harness three-turn blocker audit.

## Preserve completion and activation boundaries

- The adapter may remind the agent that the user alone decides goal achievement and that agent assessment cannot call `update_goal(status: "complete")`.
- A turn-ending adapter cannot prevent an unauthorized completion transition that occurs earlier. Treat a pre-tool transition guard as a separate candidate and authority decision.
- Creating and testing the script does not authorize adding it to `hooks.json`. Registration must coexist with every existing lifecycle handler and requires explicit user authority.

## Validate polarities

Test active first pass, recursive pass, non-active statuses, missing session row, missing or invalid database, malformed payload, exact stdout JSON, silent stderr, unchanged database bytes, and unchanged live hook configuration. Do not register the hook merely to test the artifact.
