# Approach contract

## Identity

- Candidate: `render-hook-decision-failures`
- Variant: `variant-001-typed-resolution-result`
- Classification: `instruction-gap`, `resource-gap`

## Required behavior

Return a typed success-or-failure result from each policy decision and render it once at the hook boundary.

Model `status`, `stage`, `code`, `condition`, `expected`, `received`, `candidate_count`, and optional `artifact` as explicit fields. Keep success and failure mutually exclusive. Require nonempty diagnostic text, accept only bounded domain-selected values, normalize home paths, and serialize only a valid Codex `PostToolUse` envelope.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `scripts/render_hook_decision.py`
- `references/decision-result-schema.json`

## Relationships

- `design-command-observability`: `possible-shared-foundation`
- `maintain-living-goal`: `canonical-owner`
- `resolve-managed-goal-artifacts`: `upstream-result-source`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- one exact fixture for every failure code
- success path contains no failure language
- stdout remains one valid `PostToolUse` JSON object and stderr remains empty
- condition, expected, received, stage, and code are nonempty
- malformed and unsafe input renders a bounded generic diagnostic

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit; never commit one renderer variant alone.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
