# Approach contract

## Identity

- Candidate: `persist-pending-creation-batches`
- Variant: `variant-002-write-ahead-batch-manifest`
- Classification: `instruction-gap`, `conflict-or-duplication`

## Required behavior

Freeze the complete root set and validation state in a write-ahead manifest before staging the one batch commit.

Hash every candidate root plus inventory and validation evidence, persist the immutable intended commit set and precommit OID, require staged names and current hashes to match, commit once, and append the resulting hash to a separate result record without editing candidate metadata or the manifest.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `scripts/verify_creation_batch.py`
- `references/creation-batch.schema.json`
- `references/creation-batch-result.schema.json`

## Relationships

- `auto-skill-creator`: `canonical-owner`
- `review-pending-skills`: `history-consumer`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- manifest determinism
- post-manifest file drift
- extra or missing staged path
- malformed manifest schema
- stale validation evidence and index/worktree divergence
- commit hash append after success
- rejected multi-commit transition

## Git and activation boundary

This candidate and every other candidate from the invocation are the subject of one creation-batch commit.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
