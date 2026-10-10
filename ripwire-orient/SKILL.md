---
name: ripwire-orient
description: >
  Landing COLD in an unfamiliar repo or subsystem, or about to open several files for one question:
  map first, read only the files it ranks highest. Main subsystems and entry points, 'how does X work
  / where is Y'; compacted mid-task, rebuild what you knew. A NAMED symbol → navigate. Stop at the
  first rung that answers.
allowed-tools: Bash, Read
---

> Modified canonical port: compact instructions and conditional references are maintained in `~/agentic-skills`; upstream skill-definition enhancements use `$manage-ripwire-skills`.
# Orient only as far as the current question needs

Choose the cheapest query that can answer. A known symbol belongs to `ripwire-navigate`; a symptom to `ripwire-find-bug`. Do not load the whole routing/quality/test portfolio for future phases or reread this unchanged contract for each query.

| Need | First useful query |
| --- | --- |
| An unfamiliar repository's main structure | `ripwire <dir> --report` |
| Where a specific task belongs | `ripwire <dir> --for="<task>"` |
| A literal or a selected full symbol body | `--grep=STR` or `--expand=path:name` |
| One task bundle under a budget | `--pack-task="<task>" --token-budget=N` |
| Relevant existing documentation | `--recall="<question>"` on its known directory |
| A symbol missing from the map | `--skipped`, then `--doctor` if needed |

Read the query's honesty signals. A named-symbol `--for` answer may already include its full body; avoid an identical follow-up read unless the harness or user requires it. A conceptual compact result needs one selected `--expand`, not every ranked file. `amb=` means guessed edges; `skipped_oversize=` and ignored files limit absence claims. Honor required whole owner-file reads before ownership or architecture decisions.

Stop when the question is answered. For deeper maps, communities, task partitioning, visual/export modes, field notes, or code-state recovery after actual context loss, load [orientation-reference.md](orientation-reference.md) at that condition. Existing authority must be restored first; docs and current source do not supersede protected user selections. `--situ` reads the worktree and is outside staged-only inspection.

For a mid-task read/whole-symbol edit or portable artifact workflow, load [map-before-you-read.md](map-before-you-read.md). For a body-detail/token squeeze, load [compress-ladder.md](compress-ladder.md). Those are separate conditions, not a request to read every companion.

Notes, dumps, exports, edits, delegation, installation, and hooks require their own task authority. Do not create a note or scratch knowledge base merely because orientation ran. Report only the structure and limits needed for the current decision.
