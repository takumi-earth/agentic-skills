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

The lexical invocation path is not runtime authority either: direct canonical registration, copied launchers, and renamed wrappers invalidate installation-layout inference from `argv[0]`.

## Execute the topology matrix

1. Identify the target package, package-relative real entry point, arguments, runtime root, canonical repository, and declared sibling packages.
2. Confirm the target is stateful or deployment-sensitive. Do not run this workflow for a stateless package or merely because links will be synchronized.
3. Run `scripts/validate_runtime_topology.py`; it creates and cleans its own disposable topology repositories under the selected canonical repository's `.scratchpad/`. Use `--scratch-root` for an explicitly selected existing scratch directory; keep it outside the target and sibling packages.
4. Execute the same real entry point and arguments under:
   - canonical-direct;
   - copied;
   - relative-symlink;
   - absolute-symlink.
5. Compare process exit status, normalized JSON results, and actual output artifacts, including bytes, types, permissions, and link targets. Accept an empty `side_effects` array for read-only targets. Check declarations against observed output and reject fixture changes outside the current task-output root.
6. Require canonical repository and runtime snapshots, including empty directories and permissions, to remain unchanged. Stop later topology runs after an observed protected-state or fixture mutation and report those runs as unexecuted. Exclude only the validator's own temporary directory during execution, then compare the full protected trees after cleanup.
7. Run the missing-authority, missing-sibling, and resolved-package-parent negative cases.

## Preserve scope and authority

- Confine generated fixture repositories and output to automatically cleaned temporary roots.
- Treat success as parity of the reported results and observed artifacts. Snapshot checks do not prevent writes or detect arbitrary external writes and changes reverted between observations; run only targets whose effects are already authorized.
- Use the environment-selected Python interpreter; do not hard-code an interpreter path.
- Render paths beneath the user home as `~/...`.
- Do not execute arbitrary entry points during `$link-agentic-skills` synchronization.
- Do not register hooks, edit configuration, synchronize skills, stage, commit, or publish as an implied effect of this validation.

## Load resources

- Read `references/authority-topology-contract.md` before executing a target.
- Read `references/target-output-contract.md` before interpreting target stdout or side effects.
- Run `python3 scripts/validate_runtime_topology.py --self-test --scratch-root ~/agentic-skills/.scratchpad` before relying on the validator and report assertions separately from process exit status. Self-tests require an explicit scratch destination.
- From the canonical package, run `python3 scripts/test_validate_runtime_topology.py` after changing the validator to exercise its CLI regressions.
