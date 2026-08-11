# Intent: variant-001-typed-resolution-result

## Concrete use

Render every hook policy or resolution failure with the exact checked condition, expected value, received value, failure stage, and stable machine-readable code.

## Preserved approach

Return a typed success-or-failure result from each policy decision and render it once at the hook boundary.

Model `status`, `stage`, `code`, `condition`, `expected`, `received`, `candidate_count`, and optional `artifact` as explicit fields. Require nonempty diagnostic text, accept only bounded domain-selected values, normalize home paths, keep success and failure mutually exclusive, and serialize only a valid Codex `PostToolUse` envelope without losing the typed diagnostic.

## Difference from sibling variants

Keep this approach distinct from `variant-002-structured-failure-exceptions`, `variant-003-stage-code-value-map`, `variant-004-stderr-audit-and-context`. Do not converge implementation authority, activation effects, or failure semantics merely because common text could be shared.

## Causal evidence

The hook collapsed distinct resolver failures into the false-sounding statement that the structured objective did not expose an exact file. The message hid that the objective was correct and that the hook had derived the wrong root.

- `live user correction` at `current-session JSONL line 464`: The error must explicitly state the condition checked, what was expected, and what was received.
- `direct source inspection` at `~/agentic-skills/auto-skill-enhancer/scripts/goal_completion_hook.py:132-140`: All resolution failures use one generic additionalContext message.
- `durable RCA` at `instructions/004-root-cause.json`: Expected ~/.codex/attachments with one candidate; received ~/attachments with zero candidates.

## Validation planned

- one exact fixture for every failure code
- success path contains no failure language
- stdout remains one valid `PostToolUse` hook JSON object and stderr remains empty
- condition, expected, received, stage, and code are never omitted or empty
- unsafe, unbounded, or malformed decision values become a safe typed renderer diagnostic

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
- future merge into maintain-living-goal could change completion-handoff diagnostic text
