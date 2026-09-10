# Rollout index query schema

The CLI accepts flat normalized objects and Codex `response_item` or `event_msg` envelopes with an object-valued `payload`. The package-owned `scripts/rollout_records.py` implements these adapters. Arbitrary message content is never searched for event metadata:

- source locator: the one-based physical LF-delimited input line; `raw_ordinal` or `ordinal` is a separate integer field on the outer record, with Boolean values excluded;
- kind: event-level `kind`, `type`, or `event_type`, in that precedence order;
- tool: event-level `tool_name`, `tool`, or `name` on supported tool records;
- call identity: event-level `call_id` or `tool_use_id`, with `id` as a fallback on call records only;
- status: event-level `status`/`state` and integer `exit_code`/`exit_status`; supported result records may also supply these fields in an object or JSON-object `output`, `result`, or `tool_response`;
- path filter: only `path`, `file_path`, `target_path`, `source_path`, `paths`, or `files` directly on the event or its object/JSON-object `arguments`;
- output filter: only `output`, `stdout`, `stderr`, `result`, or `tool_response` on supported result records; strings are searched directly and structured values as canonical JSON;
- candidate classification through `classification` or `candidate_class`.

Supported call kinds are `tool_call`, `function_call`, `custom_tool_call`, and `tool_use`; result kinds are `tool_result`, `tool_output`, `function_call_output`, and `custom_tool_call_output`. Metadata-like keys in message content, command text, and unrelated prose do not become selectors.

Each retained row contains its input line, recognized selectors, a SHA-256 hash of the original canonical JSON record, a hash of its original LF-delimited line bytes excluding LF, and a bounded `record` object or truncation descriptor. The source hash covers the exact original file bytes. Presentation normalizes home paths without changing these hashes. `emitted_source_bytes` counts original preview bytes consumed; `emitted_bytes` counts the displayed preview after normalization.

LF is the only line delimiter. CRLF remains valid JSON whitespace, and bare CR never advances a source locator. An empty file has no records. Malformed JSON, excessive parser nesting, and unsupported non-object/value records are reported explicitly. A filter with no recognized field yields no match; invalid filters, inverted ordinal ranges, and invalid limits produce structured failures.

`--max-rows` bounds retained matches. `--max-bytes` bounds the complete compact JSON response and final newline, including selectors, hashes, metadata, and diagnostics; its minimum is `128`. The renderer removes trailing diagnostics and rows as needed, recording counts and serialized item bytes in `output_omitted`. If even the remaining metadata cannot fit, it emits `status` plus `omitted: [row_count, diagnostic_count, original_response_bytes]`, explicitly omitting the full report. This compact form has no source provenance fields and cannot stand in for the original evidence.

The query never asserts that an attempted call landed. Explicit `ambiguous`, `unknown`, and `unsupported` states remain visible. Transport `completed` can coexist with a nonzero exit and does not prove operation success. Conflicting operation statuses or exit codes are `ambiguous`; a result without operation semantics is `unknown`. `completed` as the normalized operation state requires an explicit successful operation result, such as exit `0`, and still establishes neither authority nor landed state.
