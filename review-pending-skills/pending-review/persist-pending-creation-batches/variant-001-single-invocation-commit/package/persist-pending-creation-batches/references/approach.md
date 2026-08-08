# Approach contract

## Identity

- Candidate: `persist-pending-creation-batches`
- Variant: `variant-001-single-invocation-commit`
- Classification: `instruction-gap`, `conflict-or-duplication`

## Required behavior

Stage every complete candidate root created or changed by one invocation and commit the set once.

Validate all variants first, reject unrelated staged paths, stage the full root set in one path-bounded command, require no candidate-root remainder, commit once, and prohibit later edits until the initial batch commit exists.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `scripts/verify_creation_batch.py`
- `references/batch-commit-contract.md`

## Relationships

- `auto-skill-creator`: `canonical-owner`
- `review-pending-skills`: `history-consumer`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- multiple complete candidate roots
- unrelated staged path
- missing declared root
- unstaged candidate remainder
- single resulting commit

## Git and activation boundary

This candidate and every other candidate from the invocation are the subject of one creation-batch commit.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
