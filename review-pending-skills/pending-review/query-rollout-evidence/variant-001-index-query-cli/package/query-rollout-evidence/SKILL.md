---
name: query-rollout-evidence
description: "Query normalized Codex rollout indexes with schema-aware filters and explicit row and byte bounds. Use during named-session forensics when raw JSONL records are large, normalized shapes vary, or ad hoc `jq` queries fail. Keep the raw rollout authoritative and represent unsupported or ambiguous records explicitly."
---

# Query Rollout Evidence

Select exact evidence without flooding or silently normalizing away uncertainty.

## Query a normalized index

Read [the query schema](references/query-schema.md), then run:

```bash
python3 scripts/query_rollout_index.py <index.jsonl> --max-rows 50 --max-bytes 20000
```

Narrow with typed filters for ordinal range, record kind, tool name, call ID, path fragment, status, output pattern, or candidate classification. The CLI parses each JSONL record independently and preserves source line, raw ordinal when present, and stable record identity.

## Bound and classify output

Emit JSON containing matched rows, omitted-row and omitted-byte counts, filter metadata, source hash, malformed-line records, and unsupported-shape records. Truncate large payload fields with their original byte counts and hashes rather than pretending they were complete.

Do not infer that a tool call landed merely because it was attempted or that a heuristic candidate is authoritative. Keep attempted, completed, failed, ambiguous, and unsupported status distinct. Return nonzero for invalid filters or unreadable input, not for a valid zero-match query.
