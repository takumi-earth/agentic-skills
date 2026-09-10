# Rollout context packet contract

## Selection

Select one or more exact one-based JSONL lines or raw ordinals. Apply nonnegative `before` and `after` windows, deduplicate overlapping ranges, and emit records in source order.

`--line` addresses LF-delimited physical source lines, preserving CRLF whitespace without treating bare CR as a new line. `--ordinal` selects the outer record's integer `raw_ordinal` or `ordinal` field, not its physical position; fields inside payload data are excluded. Duplicate ordinal values select all matching windows and produce an explicit partial-selection diagnostic with the matching source lines.

The package-owned `scripts/rollout_records.py` recognizes flat normalized records and Codex `response_item`/`event_msg` envelopes with object payloads. Event metadata is shallow and separate from message content. Tool-call kinds are `tool_call`, `function_call`, `custom_tool_call`, and `tool_use`; result kinds are `tool_result`, `tool_output`, `function_call_output`, and `custom_tool_call_output`. Tool names come from their event-level `tool_name`, `tool`, or `name`; call IDs come from `call_id`/`tool_use_id`, with `id` fallback only for calls.

## Packet fields

- source file hash and source line;
- raw ordinal when present;
- recognized role or record kind;
- tool name and call ID when present;
- status, evidence source, and confidence;
- bounded payload with original byte count, emitted byte count, omitted byte count, and SHA-256 hash;
- parse or unsupported-shape diagnostic when applicable.

Call correlation pairs unique supported call/result records with the same call ID. Report `matched`, `partner-outside-window`, `unmatched`, `ambiguous` multiplicity, or `missing-call-id`; an ID on another record kind is only `known-id`. `partner_lines` contains source locators, never proof of operation success. `correlation_unsupported_lines` reports unparseable and non-object lines skipped during the same-file correlation scan; the declared adapter scope remains a limit on completeness.

Status distinguishes attempted calls, explicit operation results, transport completion, and uncertainty. Event-level result fields may be supplemented by an object/JSON-object `output`, `result`, or `tool_response`, never arbitrary message content. Explicit uncertainty remains visible; transport `completed` with exit `9` is operation failure, while transport completion without an operation result is `unknown`. Incompatible operation statuses or exit codes are `ambiguous`.

`--payload-bytes` bounds the preview; `--max-bytes` independently bounds the entire compact JSON response and final newline, including metadata and diagnostics, with default `20000` and minimum `128`. Trailing diagnostics or packets omitted for this budget are counted in `output_omitted`, including their serialized item bytes. If the remaining metadata cannot fit, `status` plus `omitted: [packet_count, diagnostic_count, original_response_bytes]` explicitly replaces the full report.

The file and raw-line hashes cover original bytes; raw-line hashes exclude the LF delimiter and preserve any CR. Payload hashes cover canonical JSON of the original selected value before presentation normalization. `emitted_source_bytes` counts the original preview bytes consumed; `emitted_bytes` counts the normalized display bytes. These hashes and the omission accounting do not establish semantic correctness or execution authority.

Context packets are navigation artifacts. Exact quotes, byte recovery, and final landed-effect decisions must return to the named raw JSONL records.
