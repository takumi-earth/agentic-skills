---
name: extract-nested-codex-goal-lifecycle
description: "Merge normalized Codex transcript goal events with a caller-supplied authoritative goal-status export while preserving provenance and disagreements. Use when lifecycle analysis needs current status and transcript-only extraction is insufficient or known to miss nested calls."
---

# Extract Nested Codex Goal Lifecycle

Keep attempted transcript transitions and authoritative current state separate.

## Prepare the two sources

Use the nested parser or another typed extractor to produce:

```json
{"events":[{"call_id":"call-1","line":42,"status":"complete","output_confirms":true}]}
```

Export goal status read-only using the contract in `references/authoritative-goal-record.schema.json`:

```json
{"records":[{"goal_id":"goal-1","status":"complete","observed_at":"2026-08-12T12:00:00Z"}]}
```

Run:

```bash
python3 scripts/merge_goal_lifecycle.py --goal-id goal-1 --transcript-events <events.json> --authoritative <goal-records.json>
```

The merger selects current status only from the last matching authoritative record, lists confirmed and unconfirmed transcript observations separately, and reports any confirmed transcript status that disagrees with current authority.

## Preserve failure visibility

Fail on a missing authoritative record, malformed status, duplicate timestamp ambiguity, or malformed event. Do not fall back to transcript status. Do not mutate the goal store or call a lifecycle tool.

Validate agreement, disagreement, unconfirmed calls, missing authority, multiple goals, and malformed sources. Treat the resulting report as analysis evidence, not completion authority.
