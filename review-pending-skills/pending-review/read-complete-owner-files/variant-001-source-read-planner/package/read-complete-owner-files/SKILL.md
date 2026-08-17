---
name: read-complete-owner-files
description: "Plan and track complete reads of selected UTF-8 source-owner files before architectural, ownership, lifecycle, or deletion conclusions. Use when the user explicitly requires whole-file reads instead of grep snippets, or when a disputed owner boundary can depend on initialization, public façades, mutation, cleanup, or tests outside a located symbol. Batch metadata first, read one bounded non-overlapping range per result through EOF, and use search only afterward for navigation. Do not use for routine symbol lookup in an already completed unchanged file or to force repository-wide reading."
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

The planner validates regular UTF-8 inputs, records byte counts, logical lines, hashes, newline state, resolved aliases, and byte-bounded non-overlapping line ranges. It emits no source contents.

## Read through EOF

Maintain a ledger containing `path`, `sha256`, `final_line`, `next_line`, and `complete`.

- Read exactly one planned file range in each tool result.
- Advance only through visibly complete output.
- If a result truncates, resume at the first unconfirmed line; do not restart confirmed ranges or completed siblings.
- Read an oversized logical line alone with a sufficient one-file result.
- Mark a file complete only when its final planned range reaches EOF.
- If a selected file changes, invalidate only that file's ledger entry and re-plan it.

## Navigate only after completion

After every selected owner file is complete, use `rg` for call-site navigation, cross-file reference discovery, or precise reinspection. Do not present the search result as a substitute for the completed owner read.

Do not reread a complete unchanged file after compaction or a minor edit merely to demonstrate diligence. Preserve the ledger and re-plan only changed files.

## Report proportionally

State which semantic owner files reached EOF, which hashes changed, and which later searches were navigation only. Do not persist a separate audit unless the user requests one or the active workflow intrinsically requires durable evidence.

