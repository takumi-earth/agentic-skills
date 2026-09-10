# Source-read planner variant

## Concrete intent

Make explicit whole-file source-reading requests reproducible through deterministic metadata planning and a bounded EOF ledger.

## Approach

Package a content-free UTF-8 range planner, read one file and one range per result, reuse sufficient source evidence, and use `ripwire` navigation to select files before full reads establish conceptual ownership.

## Preserved nuance

Whole-file reading applies to a selected owner set, not an entire repository. The planner emits hashes and ranges but never source bodies, and source evidence reuse does not override mandatory goal or instruction reloads after compaction.

## Relationships and uncertainty

This variant overlaps the instruction-read planner in `$resume-strict-context` and source research in `$plan-strict-work`. Review should decide whether one generalized planner should eventually replace duplicated mechanics while retaining distinct trigger contracts.

## Review questions

- Should the planner accept non-UTF-8 files as byte ranges or keep the source contract text-only?
- The corrected planner rejects duplicate resolved paths, accepts one symlink, and leaves distinct hard-link paths separate.
- Read-completion bookkeeping stays in existing task context; the planner does not authorize a persisted audit.


Both this planner and the existing instruction planner now use LF-delimited ranges and normalized operational diagnostics. The standalone resolved-path check remains distinct; no shared package or promotion is introduced.
