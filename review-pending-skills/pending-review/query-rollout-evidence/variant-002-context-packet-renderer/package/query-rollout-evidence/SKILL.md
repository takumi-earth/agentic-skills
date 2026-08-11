---
name: query-rollout-evidence
description: "Render compact chronology packets around selected Codex rollout JSONL lines or raw ordinals with explicit truncation, status, and provenance metadata. Use after evidence selectors identify relevant records and reviewers need bounded user, assistant, tool-call, and tool-result context. Do not replace the raw JSONL as authority."
---

# Query Rollout Evidence

Render reviewable context while preserving exact provenance.

## Select anchors

Read [the context-packet contract](references/context-packet.md). Supply exact source line numbers or raw ordinals and a bounded number of neighboring records:

```bash
python3 scripts/render_rollout_context.py <rollout.jsonl> --line 120 --before 2 --after 3
```

The renderer emits chronological packets for recognized user, assistant, tool-call, and tool-result records. Each packet carries source line, raw ordinal when available, record kind, call correlation, interpreted status with confidence, source hash, and payload truncation metadata.

## Preserve uncertainty

Represent malformed, unsupported, uncorrelated, and contradictory records explicitly. Do not relabel an attempted command as a landed edit, infer success from inner text when the process failed, or omit the fact that a payload was truncated.

Use the packet for navigation and review. Return to the named raw record for exact quoting, byte-level adjudication, or source-of-truth decisions.
