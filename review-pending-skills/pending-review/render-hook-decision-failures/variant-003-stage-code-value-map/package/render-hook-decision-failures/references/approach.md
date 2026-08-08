# Approach contract

## Identity

- Candidate: `render-hook-decision-failures`
- Variant: `variant-003-stage-code-value-map`
- Classification: `instruction-gap`, `resource-gap`

## Required behavior

Use a compact stable stage/code/value map suitable for both human context and downstream parsing.

Emit a concise diagnostic such as stage=resolve_goal_file, code=attachments_root_mismatch, condition=..., expected=..., received=... and keep value rendering home-relative.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `scripts/render_hook_decision.py`
- `references/diagnostic-codes.md`

## Relationships

- `design-command-observability`: `possible-shared-foundation`
- `auto-skill-enhancer`: `current-hook-consumer`
- `resolve-managed-goal-artifacts`: `resolution-result-consumer`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- stable field ordering
- home-path normalization
- null and collection rendering
- no generic fallback when known values exist

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit; never commit one renderer variant alone.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
