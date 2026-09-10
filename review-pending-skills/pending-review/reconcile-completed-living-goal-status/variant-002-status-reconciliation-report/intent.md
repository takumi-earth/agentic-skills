# Status reconciliation-report variant

## Concrete intent

Produce a deterministic, read-only report of operative goal-status contradictions before an authorized living-goal edit.

## Approach

Read an existing structured state record and one Markdown plan, track unit headings, exclude explicit history and fenced examples, and propose a status-span change only within the observation's own dimension. Ambiguous prose carries no generated replacement.

## Preserved nuance

The report proposes text reconciliation but never edits the goal or changes harness status. It records deliberately unrun verification without treating it as pending when the user excluded it.

## Relationships and uncertainty

This is a mechanical alternative to `variant-001-terminal-status-checklist`. Review should decide whether a shared status vocabulary can cover diverse living-goal formats.

## Review questions

- Generate a proposal only for an unambiguous same-dimension status span; preserve all other text and expose uncertain cases as facts requiring interpretation.
- Which plan formats beyond Markdown headings deserve support?
