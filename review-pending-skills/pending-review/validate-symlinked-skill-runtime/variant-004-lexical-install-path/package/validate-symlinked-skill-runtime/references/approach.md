# Approach contract

## Identity

- Candidate: `validate-symlinked-skill-runtime`
- Variant: `variant-004-lexical-install-path`
- Classification: `instruction-gap`, `resource-gap`

## Required behavior

Use the lexical invocation path rather than resolved __file__ to retain the installed harness location.

Capture argv[0] or the registered command path before resolution and infer state only from an explicitly guaranteed installation layout. Mark the approach as weak because direct canonical registration and copied launchers invalidate it.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `references/lexical-path-limitations.md`

## Relationships

- `link-agentic-skills`: `deployment-owner`
- `filesystem-git-observability`: `filesystem-evidence-owner`
- `resolve-managed-goal-artifacts`: `current-regression-example`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- registered symlink path
- PATH lookup
- direct script invocation
- renamed wrapper
- canonical registration negative

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
