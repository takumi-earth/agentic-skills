# Wait-budget protocol variant

## Concrete intent

Prevent context-wasting re-polling of active Codex subagents by selecting the longest supported interruptible mailbox wait and recording why another poll is necessary.

## Approach

Use a compact state protocol with explicit timeout ceilings, interruption handling, and allowed re-poll reasons. Keep spawn context selection as a prerequisite but focus the variant on wait behavior.

## Preserved nuance

Long waiting is not authority for optional work. A user message interrupts the wait and must be reconciled before the next task effect.

## Relationships and uncertainty

This differs from `variant-001-codex-orchestration-adapter` by specializing in wait budgeting. It overlaps Codex mailbox guidance and `$reconcile-live-steering`.

## Review questions

- Should the maximum timeout be discovered from tool metadata at runtime rather than recorded as a reference value?
- Which mandatory commentary cadence, if any, should cap an otherwise interruptible wait?
