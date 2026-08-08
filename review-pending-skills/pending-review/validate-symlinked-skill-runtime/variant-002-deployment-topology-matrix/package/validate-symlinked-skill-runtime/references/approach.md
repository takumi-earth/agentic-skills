# Approach contract

## Identity

- Candidate: `validate-symlinked-skill-runtime`
- Variant: `variant-002-deployment-topology-matrix`
- Classification: `instruction-gap`, `resource-gap`

## Required behavior

Treat deployment parity as a required smoke-test matrix for every stateful packaged script.

Build disposable copied and symlinked package fixtures, run the same entry point and arguments in every topology, compare normalized outputs and side-effect paths, and fail with exact expected and received topology facts.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `scripts/check_runtime_topology.py`
- `references/topology-fixture-matrix.md`

## Relationships

- `link-agentic-skills`: `deployment-owner`
- `filesystem-git-observability`: `filesystem-evidence-owner`
- `resolve-managed-goal-artifacts`: `current-regression-example`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- positive parity fixture
- deliberate __file__ parent regression
- relative versus absolute symlink parity
- no mutation outside disposable fixtures

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
