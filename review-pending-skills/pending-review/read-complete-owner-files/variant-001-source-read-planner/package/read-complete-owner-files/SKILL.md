---
name: read-complete-owner-files
description: "Plan and track complete reads of selected UTF-8 source-owner files before architectural, ownership, lifecycle, or deletion conclusions. Use when the user explicitly requires whole-file reads instead of excerpts, or when a disputed owner boundary can depend on initialization, public façades, mutation, cleanup, or tests outside a located symbol. Allow navigation to select files, batch their metadata, then read one bounded non-overlapping range per result through EOF before dependent conclusions. Do not use for routine symbol lookup in an already completed unchanged file or to force repository-wide reading."
---

# Read Complete Owner Files

Establish ownership from complete selected files, not isolated matches.

## Select the semantic owner set

- Start from the observed behavior and identify the producer, model or parser, orchestration consumer, public façade, and protecting tests that can change the conclusion.
- Select only files whose complete bodies are load-bearing. Do not substitute every file in a directory for semantic owner selection.
- Record whether the user explicitly required whole reads or the owner boundary itself makes partial reading unsafe.

## Plan ranges without emitting bodies

Run the packaged planner once for the complete selected set:

```bash
python3 scripts/plan_complete_reads.py <path>...
```

The planner validates regular UTF-8 inputs and emits only metadata: byte counts, LF-delimited lines, hashes, newline state, resolved paths, and bounded ranges. Consume ranges with an LF-based reader such as `sed -n 'START,ENDp'`; CRLF bytes remain intact, bare CR is part of a line, and an unterminated final line counts. Hashes cover original bytes. Duplicate resolved paths are rejected; one symlink is accepted, and different hard-link paths are not deduplicated.

## Read through EOF

Track `path`, `sha256`, `final_line`, `next_line`, and `complete` in existing task context. A metadata plan establishes ranges, not consumption of their bodies.

- Read exactly one planned file range in each tool result.
- Advance only through visibly complete output.
- If a result truncates, resume at the first unconfirmed line; do not restart confirmed ranges or completed siblings.
- Read an oversized logical line alone with a sufficient one-file result.
- Mark a nonempty file complete only after consuming its final range. A verified empty file has no body ranges; its zero-byte snapshot establishes empty content.
- A prior EOF read plus an exact narrow owned edit can establish current contents. Concurrent drift, broad rewriting, or needed detail lost from context can require renewed reading of that file.

## Navigate before dependent conclusions

Use `ripwire` and its applicable navigation skill as the primary source-navigation surface. Initial navigation can identify the files that need full reads. Search excerpts and graph summaries cannot replace complete selected files when confirming conceptual ownership.

Reuse still-sufficient source evidence rather than rereading merely for bookkeeping. This does not override `$resume-strict-context`: reload the exact designated active goal and applicable procedural skills after compaction as required. Source evidence and instruction reload obligations are separate.

## Report proportionally

State which semantic owner files reached EOF, which hashes changed, and which later searches were navigation only. Do not persist a separate audit unless the user requests one or the active workflow intrinsically requires durable evidence.
