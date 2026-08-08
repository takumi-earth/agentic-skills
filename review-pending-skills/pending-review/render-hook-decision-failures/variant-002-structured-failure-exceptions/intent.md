# Intent: variant-002-structured-failure-exceptions

## Concrete use

Render every hook policy or resolution failure with the exact checked condition, expected value, received value, failure stage, and stable machine-readable code.

## Preserved approach

Raise structured policy exceptions at the failure site and convert them to hook context only in main.

Define a bounded exception hierarchy carrying diagnostic fields, prevent broad exception text from becoming the public contract, and render unexpected exceptions separately from expected policy failures.

## Difference from sibling variants

Keep this approach distinct from `variant-001-typed-resolution-result`, `variant-003-stage-code-value-map`, `variant-004-stderr-audit-and-context`. Do not converge implementation authority, activation effects, or failure semantics merely because common text could be shared.

## Causal evidence

The hook collapsed distinct resolver failures into the false-sounding statement that the structured objective did not expose an exact file. The message hid that the objective was correct and that the hook had derived the wrong root.

- `live user correction` at `current-session JSONL line 464`: The error must explicitly state the condition checked, what was expected, and what was received.
- `direct source inspection` at `~/agentic-skills/auto-skill-enhancer/scripts/goal_completion_hook.py:132-140`: All resolution failures use one generic additionalContext message.
- `durable RCA` at `instructions/004-root-cause.json`: Expected ~/.codex/attachments with one candidate; received ~/attachments with zero candidates.

## Validation planned

- expected exception conversion
- unexpected exception classification
- no stack trace in hook stdout
- exact field preservation

## Uncertainty and risk

- Exposing sensitive received values without redaction.
- Making human messages too verbose for hook context.
- Allowing unstable exception strings to become machine codes.
- Assuming stderr is surfaced when the hook exits successfully.

The candidate remains pending because structural validity does not decide whether this design should be promoted or merged into an existing owner.

## Questions for review

- Does this approach preserve the narrowest semantic owner?
- Is its authority source available in every intended harness and deployment topology?
- Should shared behavior remain a relationship or later converge into an existing skill?
- Which activation effects, if any, should the user separately authorize?

## Possible activation effects

- none during pending creation
- future promotion could change hook diagnostic text and machine event shape
