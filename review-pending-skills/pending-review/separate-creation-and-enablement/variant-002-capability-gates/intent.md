# Capability-gates variant

## Concrete intent

Explore a more formal alternative to the artifact-lifecycle variant for workflows where one artifact crosses repository, installer, harness, hook, and runtime boundaries.

## Approach

Represent every effect as a capability edge with its own mutator, authority, new discoverability or execution power, and positive/negative evidence. Execute only edges explicitly granted.

## Preserved nuance

This approach detects commands that bundle creation and activation, and it treats writes through existing live projections as activation. It does not assume the lifecycle has exactly four stages.

## Differences from `variant-001-artifact-lifecycle`

The first variant is easier to use for ordinary artifact work and names four lifecycle states. This variant is more general and auditable but may be heavier; it uses a per-effect capability matrix and allows more stages.

## Review questions

- Is the matrix worth its context cost outside fragile multi-system workflows?
- Should a convergence variant keep the simple lifecycle vocabulary but add the bundled-command and live-projection tests from this approach?
