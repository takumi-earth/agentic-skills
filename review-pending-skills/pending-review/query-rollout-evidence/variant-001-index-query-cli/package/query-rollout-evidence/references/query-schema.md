# Rollout index query schema

The CLI accepts JSONL records with arbitrary objects and recognizes common fields without requiring one fixed schema:

- source locator: `line`, `line_number`, `ordinal`, or `raw_ordinal`;
- kind: `kind`, `type`, or nested event type;
- tool: `tool`, `tool_name`, or nested call name;
- call identity: `call_id` or `id` on tool records;
- status: explicit status or process exit fields;
- paths and payload text through bounded recursive scalar inspection;
- candidate classification through `classification` or `candidate_class`.

Every emitted result contains the original source line, recognized selectors, a stable SHA-256 hash of the canonical record, and a bounded `record` object or truncation descriptor.

Malformed JSON and unsupported non-object records appear in dedicated arrays. A filter with no recognized field simply yields no match; an invalid filter or negative limit is an error. Row and byte limits are applied deterministically in source order.

The query result never asserts that an attempted call landed. Status normalization preserves `attempted`, `completed`, `failed`, `ambiguous`, `unsupported`, and explicit exit-code evidence.
