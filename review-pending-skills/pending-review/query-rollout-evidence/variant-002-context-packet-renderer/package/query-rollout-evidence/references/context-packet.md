# Rollout context packet contract

## Selection

Select one or more exact one-based JSONL lines or raw ordinals. Apply nonnegative `before` and `after` windows, deduplicate overlapping ranges, and emit records in source order.

## Packet fields

- source file hash and source line;
- raw ordinal when present;
- recognized role or record kind;
- tool name and call ID when present;
- status, evidence source, and confidence;
- bounded payload with original byte count, emitted byte count, omitted byte count, and SHA-256 hash;
- parse or unsupported-shape diagnostic when applicable.

Status must distinguish attempted calls, completed tool results, explicit nonzero exits, inner text claims, and unknown shapes. When fields contradict, emit `ambiguous` and preserve the competing evidence.

Context packets are navigation artifacts. Exact quotes, byte recovery, and final landed-effect decisions must return to the named raw JSONL records.
