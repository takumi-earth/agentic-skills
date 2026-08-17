# Strict-owner integration variant

## Concrete intent

Integrate explicit complete-source-reading requirements into existing strict phase owners without adding another executable or default audit phase.

## Approach

Route file selection, EOF reading, live corrections, compaction reuse, and conclusions through `$guard-strict-work`, `$plan-strict-work`, `$implement-strict-work`, `$reconcile-live-steering`, and `$resume-strict-context`.

## Preserved nuance

The requirement is evidence-scoped: it freezes only conclusions that depend on incomplete files, preserves completed unchanged reads, and does not require repository-wide rereading.

## Relationships and uncertainty

This variant is an alternative to the standalone planner. Review should decide whether existing instruction-read tooling is sufficient for source files and whether distributed routing is reliably discoverable.

## Review questions

- Should one official phase owner become the sole entry point for this mode?
- Is a packaged source planner necessary, or can callers reuse the existing instruction planner safely?
- How should implementations account for their own narrow edits without wasteful whole-file rereads?

