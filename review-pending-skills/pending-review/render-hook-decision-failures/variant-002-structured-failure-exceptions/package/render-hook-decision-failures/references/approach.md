# Approach contract

## Identity

- Candidate: `render-hook-decision-failures`
- Variant: `variant-002-structured-failure-exceptions`
- Classification: `instruction-gap`, `resource-gap`

## Required behavior

Raise structured policy exceptions at the failure site and convert them to hook context only in main.

Define a bounded exception hierarchy carrying diagnostic fields, prevent broad exception text from becoming the public contract, and render unexpected exceptions separately from expected policy failures.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `references/structured-failure-exceptions.md`

## Relationships

- `design-command-observability`: `possible-shared-foundation`
- `auto-skill-enhancer`: `current-hook-consumer`
- `resolve-managed-goal-artifacts`: `resolution-result-consumer`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- expected exception conversion
- unexpected exception classification
- no stack trace in hook stdout
- exact field preservation

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit; never commit one renderer variant alone.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
