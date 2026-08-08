# Intent: variant-003-stage-code-value-map

## Concrete use

Render every hook policy or resolution failure with the exact checked condition, expected value, received value, failure stage, and stable machine-readable code.

## Preserved approach

Use a compact stable stage/code/value map suitable for both human context and downstream parsing.

Emit a concise diagnostic such as stage=resolve_goal_file, code=attachments_root_mismatch, condition=..., expected=..., received=... and keep value rendering home-relative.

## Difference from sibling variants

Keep this approach distinct from `variant-001-typed-resolution-result`, `variant-002-structured-failure-exceptions`, `variant-004-stderr-audit-and-context`. Do not converge implementation authority, activation effects, or failure semantics merely because common text could be shared.

## Causal evidence

The hook collapsed distinct resolver failures into the false-sounding statement that the structured objective did not expose an exact file. The message hid that the objective was correct and that the hook had derived the wrong root.

- `live user correction` at `current-session JSONL line 464`: The error must explicitly state the condition checked, what was expected, and what was received.
- `direct source inspection` at `~/agentic-skills/auto-skill-enhancer/scripts/goal_completion_hook.py:132-140`: All resolution failures use one generic additionalContext message.
- `durable RCA` at `instructions/004-root-cause.json`: Expected ~/.codex/attachments with one candidate; received ~/attachments with zero candidates.

## Validation planned

- stable field ordering
- home-path normalization
- null and collection rendering
- no generic fallback when known values exist

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
