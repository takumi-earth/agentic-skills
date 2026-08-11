# Intent: variant-001-explicit-runtime-root

## Concrete use

Separate package-resource location from harness-runtime state and validate copied, symlinked, and canonical-direct skill execution as equivalent deployment topologies.

## Preserved approach

Require harness-state roots as explicit arguments or environment variables and reserve __file__ for package resources only.

Classify every path dependency as package, harness state, repository, or task output; reject scripts that derive a harness-state root from a resolved package parent; prefer environment-selected executables and home-relative persisted paths. Execute the target's real entry point in canonical-direct, copied, relative-link, and absolute-link packages, and verify its observed runtime root, normalized output, and contained side effects.

## Difference from sibling variants

Keep this approach distinct from `variant-002-deployment-topology-matrix`, `variant-003-declared-runtime-context`, `variant-004-lexical-install-path`. Do not converge implementation authority, activation effects, or failure semantics merely because common text could be shared.

## Causal evidence

Resolving __file__ is correct for package resources but not for harness configuration or state. The installed skill symlink resolved into the canonical repository, changing the inferred parent chain and silently moving the attachments root.

- `filesystem observation` at `codex-home-environment.json`: The installed auto-skill-enhancer package is a symlink to canonical source and CODEX_HOME is ~/.codex.
- `direct source inspection` at `~/rust-forks/codex-orig/codex-rs/hooks/src/engine/command_runner.rs`: Hook commands inherit environment; runtime state need not be inferred from package location.
- `live user corrections` at `retained visible turns`: Use environment-selected python3 and render home paths as ~ rather than hard-coded interpreter or expanded home paths.

## Validation planned

- copied package
- relative symlink
- absolute symlink
- canonical-direct execution
- custom CODEX_HOME
- missing runtime-authority failure
- deliberate resolved-parent regression
- real entry-point output and side-effect containment
- no hard-coded /usr/bin interpreter

## Uncertainty and risk

- Running arbitrary package scripts during synchronization.
- Confusing canonical repository location with harness installation root.
- Overconstraining stateless packages with unnecessary topology tests.
- Retaining lexical-path inference as a known weak variant.

The candidate remains pending because structural validity does not decide whether this design should be promoted or merged into an existing owner.

## Questions for review

- Does this approach preserve the narrowest semantic owner?
- Is its authority source available in every intended harness and deployment topology?
- Should shared behavior remain a relationship or later converge into an existing skill?
- Which activation effects, if any, should the user separately authorize?

## Possible activation effects

- none during pending creation
- future promotion could add required deployment smoke tests to scripted skills
