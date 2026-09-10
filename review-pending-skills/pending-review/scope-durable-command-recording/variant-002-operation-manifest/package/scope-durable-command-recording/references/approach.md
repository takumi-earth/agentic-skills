# Approach contract

## Identity

- Candidate: `scope-durable-command-recording`
- Variant: `variant-002-operation-manifest`
- Classification: `instruction-gap`, `execution-error`

## Required behavior

Specify a task-required declaration as an adapter over the existing command recorder. Ordinary reads and focused checks do not acquire a manifest requirement.

Declare `cwd`, inputs, exact `argv`, expected conditions, operation outputs, report path, purpose, and timeout. `runner-contract.md` distinguishes supported observations from proposed enforcement; neither schema validity nor a list of outputs restricts the command's actual effects.

## Packaged specification resources

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
- declared versus enforced output scope
- passive read exemption
- nonzero diagnostic reporting

## Git and activation boundary

Use the complete candidate root for interactive correctness commits; the automatic creator retains its separate invocation-wide creation boundary.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
