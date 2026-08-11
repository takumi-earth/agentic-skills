# Context-packet-renderer variant

## Concrete intent

Render compact chronological context around selected rollout lines or ordinals with explicit provenance and truncation.

## Approach

Correlate recognized user, assistant, tool-call, and tool-result records into bounded packets carrying source line, raw ordinal, status confidence, payload hashes, and truncation metadata.

## Preserved nuance

Packets support navigation and review but never supersede raw JSONL. Contradictory, uncorrelated, malformed, and unsupported records remain visible.

## Relationships and uncertainty

This complements the index-query variant and overlaps `$filesystem-git-observability`. Review should decide how much status interpretation belongs in the renderer versus a normalized upstream indexer.
