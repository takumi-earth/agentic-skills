# Approach contract

## Identity

- Candidate: `validate-symlinked-skill-runtime`
- Variant: `variant-001-explicit-runtime-root`
- Classification: `instruction-gap`, `resource-gap`

## Required behavior

Require harness-state roots as explicit arguments or environment variables and reserve __file__ for package resources only.

Classify every path dependency as package, harness state, repository, or task output; reject scripts that derive a harness-state root from a resolved package parent; prefer env-selected executables and home-relative persisted paths.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `scripts/check_runtime_topology.py`
- `references/path-authority-model.md`

## Relationships

- `link-agentic-skills`: `deployment-owner`
- `filesystem-git-observability`: `filesystem-evidence-owner`
- `resolve-managed-goal-artifacts`: `current-regression-example`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- copied package
- relative symlink
- absolute symlink
- canonical-direct execution
- custom CODEX_HOME
- no hard-coded /usr/bin interpreter

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
