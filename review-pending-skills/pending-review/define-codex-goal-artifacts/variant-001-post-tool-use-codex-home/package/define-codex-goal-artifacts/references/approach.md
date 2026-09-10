# Approach contract

## Identity

- Candidate: `define-codex-goal-artifacts`
- Variant: `variant-001-post-tool-use-codex-home`
- Classification: `not-a-skill-issue`, `speculative architecture candidate`

## Required behavior

Supply one versioned `runtime_context.codex_home` through a trusted `PostToolUse` input profile. Derive `attachments` from that root; do not create competing root fields.

Read `post-tool-use-schema.md` for exact fields, namespace/home binding, profile negotiation, and failure behavior. This removes package-topology root inference only; exact artifact identity and user authority remain separate. Read `source-change-map.md` when planning integration against the attributed source revision.

## Resources

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

Use the interactive review owner's complete candidate-root commit contract for an authorized correction. The automatic creator's invocation-wide commit rule applies only to automatic creation. This specification does not authorize editing `~/rust-forks/codex-orig`.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
