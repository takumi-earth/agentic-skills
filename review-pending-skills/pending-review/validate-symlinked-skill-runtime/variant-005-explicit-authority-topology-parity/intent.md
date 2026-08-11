# Intent: variant-005-explicit-authority-topology-parity

## Concrete use

Validate a stateful packaged skill's real entry point across canonical-direct, copied, relative-symlink, and absolute-symlink deployments while keeping package resources, harness state, canonical repository state, and task output under separate explicit authorities.

## Converged approach

Combine `variant-001-explicit-runtime-root`'s authority separation with `variant-002-deployment-topology-matrix`'s executable parity fixtures.

Require the target entry point and its declared sibling-package dependencies. Execute identical arguments in disposable topology repositories with explicit `CODEX_HOME`, canonical-repository, and task-output values. Compare process status, normalized JSON output, and declared side-effect paths. Reproduce sibling dependencies in copied and linked repositories, reject missing authority, and prove a resolved-package-parent regression and a missing sibling fail.

## Difference from predecessor and sibling variants

- Adopt explicit harness-state authority and package-resource separation from variant `001`.
- Adopt real-entry-point topology execution, output comparison, and side-effect containment from variant `002`.
- Add explicit canonical-repository authority and declared sibling-package fixture reproduction.
- Confine all generated topology repositories and target output to automatically cleaned temporary roots.
- Defer variant `003`'s launcher-manifest protocol and retain variant `004` only as rejected lexical-topology evidence.

## Causal evidence

Resolving `__file__` is correct for package resources but not for harness configuration or state. The installed skill symlink resolved into the canonical repository, changing the inferred parent chain and silently moving the attachments root.

- `filesystem observation` at `codex-home-environment.json`: The installed `$auto-skill-enhancer` package is a symlink to canonical source and `CODEX_HOME` is `~/.codex`.
- `direct source inspection` at `~/rust-forks/codex-orig/codex-rs/hooks/src/engine/command_runner.rs`: Hook commands inherit environment; runtime state need not be inferred from package location.
- `approved pending-skill review plan` at `active living goal`: Converge variants `001` and `002`, exercise real entry points, add missing-authority and resolved-parent negatives, and reproduce declared sibling dependencies.

## Validation planned

- canonical-direct, copied, relative-symlink, and absolute-symlink parity
- custom `CODEX_HOME` and explicit canonical repository state
- missing runtime authority
- deliberate resolved-package-parent regression
- declared sibling package in every fixture topology
- missing sibling-package failure
- normalized exit status, output, and side-effect parity
- no canonical repository or runtime mutation
- automatic disposal of every generated fixture write

## Negative trigger boundary

Do not use this skill for stateless packages whose behavior has no deployment-sensitive state or package-resource dependency. Do not invoke it merely to synchronize links; `$link-agentic-skills` owns link synchronization and its own convergence checks.

## Possible activation effects

- none during pending creation
- future promotion could add deployment-runtime validation for stateful scripted skills
