# Approach contract

## Identity

- Candidate: `scope-durable-command-recording`
- Variant: `variant-002-operation-manifest`
- Classification: `instruction-gap`, `execution-error`

## Required behavior

Require every substantive operation to be declared in a durable argv manifest consumed by one generic runner.

Persist cwd, inputs, exact argv, expected conditions, outputs, and timeout before execution; keep passive reads outside the manifest; refuse shell interpolation and unlisted side effects.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `references/operation-manifest.schema.json`
- `references/runner-contract.md`

## Relationships

- `filesystem-git-observability`: `possible-operational-owner`
- `design-command-observability`: `possible-policy-owner`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- exact argv preservation
- home-path normalization
- undeclared output rejection
- passive read exemption
- nonzero diagnostic reporting

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
