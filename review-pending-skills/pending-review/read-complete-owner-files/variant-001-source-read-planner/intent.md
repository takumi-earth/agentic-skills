# Source-read planner variant

## Concrete intent

Make explicit whole-file source-reading requests reproducible through deterministic metadata planning and a bounded EOF ledger.

## Approach

Package a content-free UTF-8 range planner, read one file and one range per result, invalidate only changed hashes, and permit `rg` only as navigation after the selected semantic owners are complete.

## Preserved nuance

Whole-file reading applies to a selected owner set, not an entire repository. The planner emits hashes and ranges but never source bodies, and a complete unchanged file is not reread merely because context compacted.

## Relationships and uncertainty

This variant overlaps the instruction-read planner in `$resume-strict-context` and source research in `$plan-strict-work`. Review should decide whether one generalized planner should eventually replace duplicated mechanics while retaining distinct trigger contracts.

## Review questions

- Should the planner accept non-UTF-8 files as byte ranges or keep the source contract text-only?
- Should symlink aliases be rejected, as this variant does, or represented as distinct lexical inputs?
- Should a promoted form persist the ledger or leave ledger storage to the calling workflow?

