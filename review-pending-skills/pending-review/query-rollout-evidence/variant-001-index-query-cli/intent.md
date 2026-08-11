# Index-query-CLI variant

## Concrete intent

Query normalized rollout indexes with typed selectors and bounded output instead of brittle ad hoc JSON assumptions.

## Approach

Parse JSONL records independently, filter by ordinal, kind, tool, call, path, status, output, or classification, and emit matched rows with locators, source hashes, malformed or unsupported states, and omitted-output accounting.

## Preserved nuance

Normalized indexes are navigation aids. The raw rollout remains authoritative, and attempted, completed, landed, failed, ambiguous, and unsupported records remain distinct.

## Relationships and uncertainty

This overlaps `$audit-rollout-damage`, `$skill-researcher`, and `$design-command-observability`. Review should decide whether adapters for particular index schemas should be siblings.
