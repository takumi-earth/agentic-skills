# Approach contract

## Identity

- Candidate: `scope-durable-command-recording`
- Variant: `variant-001-effect-classification`
- Classification: `instruction-gap`, `execution-error`

## Required behavior

Classify each command by effect and require durable machinery only for computation, transformation, decision, mutation, or audit evidence production.

Allow direct passive reads, require a durable script plus persisted report for substantive operations, name the classification in the run ledger, and escalate ambiguous multi-step shell logic to a script before execution.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `scripts/classify_command_recording.py`
- `references/effect-classification.md`

## Relationships

- `filesystem-git-observability`: `possible-operational-owner`
- `design-command-observability`: `possible-policy-owner`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- passive SKILL.md read
- source search with computed selection
- multi-file mutation
- Git-state decision
- ambiguous pipeline

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
