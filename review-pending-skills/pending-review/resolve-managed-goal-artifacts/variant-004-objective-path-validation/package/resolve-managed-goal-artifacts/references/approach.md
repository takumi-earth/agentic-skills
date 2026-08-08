# Approach contract

## Identity

- Candidate: `resolve-managed-goal-artifacts`
- Variant: `variant-004-objective-path-validation`
- Classification: `resource-gap`

## Required behavior

Parse the exact absolute path already present in objective prose, infer its attachment root, and cross-check it against the configured harness root.

Extract exact path tokens rather than enumerate sibling attachment directories, require an attachments/<uuid>/<file> shape, compare the inferred root with CODEX_HOME or ~/.codex, and reject mismatches with explicit expected and received values.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `scripts/resolve_goal_artifact.py`
- `references/objective-path-grammar.md`

## Relationships

- `auto-skill-enhancer`: `possible-enhancement-owner`
- `maintain-living-goal`: `goal-file-consumer`
- `define-codex-goal-artifacts`: `typed-contract-alternative`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- exact current wrapper string
- spaces and punctuation in file names
- two path tokens
- root mismatch
- path traversal and symlink escape

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit with every other candidate produced by this invocation; do not commit variants separately.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
