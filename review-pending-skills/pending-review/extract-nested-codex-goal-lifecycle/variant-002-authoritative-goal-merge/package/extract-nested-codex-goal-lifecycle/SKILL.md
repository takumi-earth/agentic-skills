---
name: extract-nested-codex-goal-lifecycle
description: "Merge normalized Codex transcript goal events with a caller-supplied authoritative goal-status export while preserving provenance and disagreements. Use when lifecycle analysis needs current status and transcript-only extraction is insufficient or known to miss nested calls."
---

# Extract Nested Codex Goal Lifecycle

Keep attempted transcript transitions and authoritative current state separate.

## Prepare the two sources

Use the nested parser or another typed extractor to produce:

```json
{"events":[{"goal_id":"goal-1","thread_id":"thread-1","call_id":"call-1","line":42,"timestamp":"2026-08-12T11:00:00Z","status":"complete","output_confirms":true}]}
```

Export goal status read-only using the contract in `references/authoritative-goal-record.schema.json`:

```json
{"records":[{"goal_id":"goal-1","thread_id":"thread-1","status":"complete","observed_at":"2026-08-12T12:00:00Z"}]}
```

Run:

```bash
python3 scripts/merge_goal_lifecycle.py --goal-id goal-1 --thread-id thread-1 --transcript-events <events.json> --authoritative <goal-records.json>
```

The merger selects current status only from the latest uniquely timestamped authoritative record for the exact goal and thread. It compares parsed instants, including timezone offsets. All authority records must satisfy the schema; use a date-time format checker with an external schema validator.

It accepts the official `$skill-researcher` `nested_goal_call_site` shape: `arguments.status`, `output_confirmation`, source locators, and `output.goal`. The `confirmed` state requires a consistent returned goal status. Preserve missing, ambiguous, unattributed, unsupported, failed, and status-mismatch observations; an outer call ID alone is not confirmation. Legacy `output_confirms` is explicitly caller-declared evidence.

Bind `goal_id` and `thread_id` through explicit fields or those exact fields in a confirmed returned goal. Missing attribution stays unresolved; conflicting declared and returned identities are preserved separately. The official extractor may not emit those identities, so do not infer them from a selected goal, ordinal, or outer call ID. Caller-supplied identity and authority exports are not independently authenticated.

`timestamp` locates the transcript observation. Optional `state_at` explicitly identifies the instant at which the reported state was observed. Only a confirmed, attributed status with `state_at` equal to the authority's `observed_at` can disagree with that snapshot. Earlier transitions remain history, and later or untimed observations are not contradictions with an earlier snapshot. Both input hashes cover the exact bytes parsed.

## Preserve failure visibility

Fail on a missing authoritative record, malformed status, duplicate timestamp ambiguity, or malformed event. Do not fall back to transcript status. Do not mutate the goal store or call a lifecycle tool.

Validate agreement, disagreement, unconfirmed calls, missing authority, multiple goals, and malformed sources. Treat the resulting report as analysis evidence, not completion authority.
