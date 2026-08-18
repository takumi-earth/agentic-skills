---
name: extract-nested-codex-goal-lifecycle
description: "Extract Codex goal lifecycle calls nested inside functions.exec rollout records and correlate them with custom tool outputs. Use when normalized session evidence misses update_goal events because the call is embedded in JavaScript rather than represented as a top-level tool item."
---

# Extract Nested Codex Goal Lifecycle

Parse typed rollout records before searching text. Never use a broad transcript grep as lifecycle proof.

## Extract nested calls

Run:

```bash
python3 scripts/extract_nested_goal_events.py --transcript <rollout.jsonl>
```

The script:

- reads only `response_item` records whose payload is a completed custom `exec` call;
- finds `tools.update_goal(...)` outside JavaScript strings, template literals, and comments;
- extracts only quoted `complete` or `blocked` status values;
- correlates each outer call ID with its `custom_tool_call_output` record;
- reports call observation and output confirmation separately.

Treat `output_confirms: true` as transcript evidence that the matching tool output contained the requested goal status. Do not infer authoritative current status from an unconfirmed call or from transcript evidence alone when the harness goal store is available.

## Validate false-positive resistance

Test a real nested call, the same text in an assistant message, a quoted JavaScript string, line and block comments, two calls in one input, missing output, mismatched output status, malformed JSONL, and an ordinary top-level tool record. Preserve line numbers and call IDs in every finding.

This skill is read-only. It must not invoke a goal lifecycle tool or change the transcript.
