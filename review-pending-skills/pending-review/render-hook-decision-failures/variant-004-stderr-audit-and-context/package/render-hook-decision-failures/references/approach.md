# Approach contract

## Identity

- Candidate: `render-hook-decision-failures`
- Variant: `variant-004-stderr-audit-and-context`
- Classification: `instruction-gap`, `resource-gap`

## Required behavior

Keep hook stdout schema minimal while recording a machine audit event on stderr and an actionable human message in additionalContext.

Render identical diagnostic facts to both channels without changing the hook exit status or contaminating stdout JSON. Explicitly mark that Codex may not surface successful-hook stderr, so additionalContext remains required.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `references/hook-channel-contract.md`

## Relationships

- `design-command-observability`: `possible-shared-foundation`
- `auto-skill-enhancer`: `current-hook-consumer`
- `resolve-managed-goal-artifacts`: `resolution-result-consumer`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- stdout parses independently
- stderr event contains matching diagnostic code
- exit zero remains non-blocking
- additionalContext remains actionable when stderr is discarded

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit; never commit one renderer variant alone.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
