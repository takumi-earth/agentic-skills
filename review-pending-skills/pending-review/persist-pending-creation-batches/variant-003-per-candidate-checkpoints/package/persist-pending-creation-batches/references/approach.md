# Approach contract

## Identity

- Candidate: `persist-pending-creation-batches`
- Variant: `variant-003-per-candidate-checkpoints`
- Classification: `instruction-gap`, `conflict-or-duplication`

## Rejected hypothetical behavior

The rejected strategy would persist each complete candidate root separately as soon as it validates. This statement documents the comparison subject; it is not an instruction to stage or commit.

Retain the superseded per-candidate checkpoint design for comparison, explicitly record the user's rejection and the fragmentation cost, and never execute it during the controlling grouped-commit workflow.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `references/per-candidate-checkpoint-tradeoffs.md`

## Relationships

- `auto-skill-creator`: `canonical-owner`
- `review-pending-skills`: `history-consumer`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- demonstrate commit-count growth
- compare recovery granularity
- confirm variant remains pending and inactive

Do not run this comparison as an active batch workflow.

## Git and activation boundary

This candidate and every other candidate from the invocation are the subject of one creation-batch commit.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
