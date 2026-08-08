# Approach contract

## Identity

- Candidate: `render-hook-decision-failures`
- Variant: `variant-001-typed-resolution-result`
- Classification: `instruction-gap`, `resource-gap`

## Required behavior

Return a typed success-or-failure result from each policy decision and render it once at the hook boundary.

Model stage, code, condition, expected, received, and evidence as explicit fields; keep success and failure mutually exclusive; serialize one valid hook response without losing the typed diagnostic.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `scripts/render_hook_decision.py`
- `references/decision-result-schema.json`

## Relationships

- `design-command-observability`: `possible-shared-foundation`
- `auto-skill-enhancer`: `current-hook-consumer`
- `resolve-managed-goal-artifacts`: `resolution-result-consumer`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- one exact fixture for every failure code
- success path contains no failure language
- stdout remains one valid hook JSON object
- condition, expected, and received are never omitted

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit; never commit one renderer variant alone.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
