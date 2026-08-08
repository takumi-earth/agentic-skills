# Approach contract

## Identity

- Candidate: `define-codex-goal-artifacts`
- Variant: `variant-001-post-tool-use-codex-home`
- Classification: `not-a-skill-issue`, `speculative architecture candidate`

## Required behavior

Add codex_home or attachments_root to the versioned PostToolUse event context.

Extend hook schema construction at the runtime boundary, serialize the configured root home-relatively where appropriate, retain backwards compatibility for handlers that ignore the field, and document trust and platform semantics.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `references/post-tool-use-schema.md`
- `references/source-change-map.md`

## Relationships

- `~/rust-forks/codex-orig`: `authoritative-source-checkout`
- `resolve-managed-goal-artifacts`: `downstream-consumer`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- schema serialization fixture
- old handler compatibility
- custom CODEX_HOME
- resume and fork event parity

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit; do not edit ~/rust-forks/codex-orig during pending creation.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
