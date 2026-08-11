# Approach contract

## Identity

- Candidate: `validate-symlinked-skill-runtime`
- Variant: `variant-002-deployment-topology-matrix`
- Classification: `instruction-gap`, `resource-gap`

## Required behavior

Treat deployment parity as a required smoke-test matrix for every stateful packaged script.

Build disposable copied, relative-symlink, and absolute-symlink fixtures around the canonical package. Run the target's real entry point in every topology, compare exit status and normalized output, validate declared side-effect containment, and prove the canonical package and runtime state remain unchanged.

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
- real entry-point output and declared side-effect parity
- unchanged canonical package and runtime state
- no mutation outside disposable fixtures

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
