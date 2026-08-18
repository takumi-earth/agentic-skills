# Status reconciliation-report variant

## Concrete intent

Produce a deterministic, read-only report of operative goal-status contradictions before an authorized living-goal edit.

## Approach

Read a structured current-state ledger and one Markdown plan, track unit headings, exempt only explicitly delimited history, and emit each stale line with its evidence-backed proposed current status.

## Preserved nuance

The report proposes text reconciliation but never edits the goal or changes harness status. It records deliberately unrun verification without treating it as pending when the user excluded it.

## Relationships and uncertainty

This is a mechanical alternative to `variant-001-terminal-status-checklist`. Review should decide whether a shared status vocabulary can cover diverse living-goal formats.

## Review questions

- Should proposal text be generated or should the report expose only contradiction facts?
- Which plan formats beyond Markdown headings deserve support?
