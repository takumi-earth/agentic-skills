# Settled-unit linter variant

## Concrete intent

Detect operative reassessment, re-verification, and renewed countersignature language added for already settled decision units.

## Approach

Read an existing caller-supplied unit ledger and Markdown document, track heading scope, exclude explicit history and fenced examples, distinguish prohibitions and guard checks from decision reassessment, and emit deterministic advisory findings without changing either input.

## Preserved nuance

The linter checks a bounded English vocabulary, not decision truth. Unqualified reassessment remains `needs-context`; a clean scan is limited to supported signals. A ledger entry must carry attributable user provenance; the script does not create settled authority from a label or authorize another ledger.

## Relationships and uncertainty

This is a mechanical alternative to `variant-001-verdict-state-machine`. Review should decide whether explicit history delimiters are acceptable in living plans or too intrusive.

## Review questions

- Should the linter accept structured Markdown tables as history regions?
- Which reopening phrases belong in the minimal high-signal vocabulary?
