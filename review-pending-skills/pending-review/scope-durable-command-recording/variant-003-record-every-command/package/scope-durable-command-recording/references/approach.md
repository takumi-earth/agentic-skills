# Approach contract

## Identity

- Candidate: `scope-durable-command-recording`
- Variant: `variant-003-record-every-command`
- Classification: `instruction-gap`, `execution-error`

## Required behavior

Wrap every command, including passive reads, in a durable task-local script.

Retain the overbroad approach as rejected comparison evidence, record its avoidable indirection and interface-drift cost, and prohibit it from controlling current execution.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `references/record-every-command-tradeoffs.md`

## Relationships

- `filesystem-git-observability`: `possible-operational-owner`
- `design-command-observability`: `possible-policy-owner`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- measure wrapper overhead
- reproduce unsupported-flag failure
- confirm pending inactive status

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
