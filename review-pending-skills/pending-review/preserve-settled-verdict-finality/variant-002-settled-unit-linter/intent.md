# Settled-unit linter variant

## Concrete intent

Detect operative reassessment, re-verification, and renewed countersignature language added for already settled decision units.

## Approach

Read a caller-supplied unit ledger and Markdown document, track unit headings, exempt only explicitly delimited historical regions, and emit deterministic findings without changing either input.

## Preserved nuance

The linter checks text consistency, not decision truth. A ledger entry must carry user provenance; the script does not create settled authority from a label.

## Relationships and uncertainty

This is a mechanical alternative to `variant-001-verdict-state-machine`. Review should decide whether explicit history delimiters are acceptable in living plans or too intrusive.

## Review questions

- Should the linter accept structured Markdown tables as history regions?
- Which reopening phrases belong in the minimal high-signal vocabulary?
