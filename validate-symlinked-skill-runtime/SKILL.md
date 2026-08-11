---
name: validate-symlinked-skill-runtime
description: "Validate a stateful skill's real entry point across canonical-direct, copied, relative-symlink, and absolute-symlink deployments with explicit runtime and repository authority. Use after changing a packaged script whose behavior depends on harness state, package resources, repository state, task output, or declared sibling packages; do not use for stateless packages or for link synchronization itself."
---

# Validate Symlinked Skill Runtime

Validate deployment-sensitive skill behavior without conflating package location, harness state, canonical repository state, or task output.

## Separate every path authority

Classify and supply each dependency independently:

- **Package resources:** Resolve only resources shipped with the target package from its package location.
- **Harness state:** Supply `CODEX_HOME` or the target's corresponding explicit runtime variable. Never derive it from resolved package parents.
- **Canonical repository state:** Supply the canonical repository root explicitly when the target reads repository-owned state. Do not substitute a copied or linked package parent.
- **Task output:** Select a disposable output root and require every declared side effect beneath it.

Treat a declared sibling package as a package-resource dependency. Reproduce that sibling under the same lexical repository layout in copied, relative-link, and absolute-link fixtures. Test the missing-sibling failure separately.

## Execute the topology matrix

1. Identify the target package, package-relative real entry point, arguments, runtime root, canonical repository, and declared sibling packages.
2. Confirm the target is stateful or deployment-sensitive. Do not run this workflow for a stateless package or merely because links will be synchronized.
3. Run `scripts/validate_runtime_topology.py`; it creates and cleans its own disposable topology repositories.
4. Execute the same real entry point and arguments under:
   - canonical-direct;
   - copied;
   - relative-symlink;
   - absolute-symlink.
5. Compare process exit status and normalized JSON output. Require the target to report every side-effect path and keep each path within the topology's task-output root.
6. Require the canonical repository and runtime state hashes to remain unchanged.
7. Run the missing-authority, missing-sibling, and resolved-package-parent negative cases.

## Preserve scope and authority

- Confine generated fixture repositories and output to automatically cleaned temporary roots.
- Use the environment-selected Python interpreter; do not hard-code an interpreter path.
- Render paths beneath the user home as `~/...`.
- Do not execute arbitrary entry points during `$link-agentic-skills` synchronization.
- Do not register hooks, edit configuration, synchronize skills, stage, commit, or publish as an implied effect of this validation.

## Load resources

- Read `references/authority-topology-contract.md` before executing a target.
- Read `references/target-output-contract.md` before interpreting target stdout or side effects.
- Run `python3 scripts/validate_runtime_topology.py --self-test` before relying on the validator and report assertions separately from process exit status.
