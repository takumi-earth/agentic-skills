# Integration Preparation

Load this reference when an integration must consume upgraded and repaired dependency shapes. Routine lock maintenance or integration without that prerequisite does not need this pattern.

## Preserve the required predecessor state

Read the selected target policy, supported build surface, and public workflow boundary. If preparation belongs to the first public `apply`, keep it there; do not silently move required work into a manual prerequisite.

Preserve this chain where the task requires its stages:

```text
toolchain/edition alignment
    -> dependency requirements and graph resolution
    -> upgrade-related compatibility repairs
    -> integration seams against repaired shapes
    -> final dependency/lock convergence
    -> authorized verification
```

Assign each repair and integration seam its actual prerequisites. Stage names and final-state equivalence do not justify consuming a source shape before its repair exists.

## Keep dependency maintenance with its owner

Use the selected dependency manager through the authorized orchestration boundary. Deterministic repair jobs own explicit source or configuration transformations; they do not implement graph resolution or hand-edit lock graphs. New diagnostics inform owner-level investigation, not automatic source-mutation specifications.

Preserve the task's selected requirement and resolution commands. For a Cargo policy that explicitly selects latest incompatible and pinned-requirement upgrades, examples include `cargo upgrade --recursive --incompatible --pinned` and `cargo update --recursive`; conservative `cargo update --workspace` or an older dependency pin is not a substitute for that policy. Do not import those examples into a different policy or add maintenance for an excluded build system.

## Refresh affected inputs after real effects

After a dependency tool changes manifests, lock state, or relevant source, reload the affected inputs before dependent planning. Refresh semantic indexes, captures, and preconditions that depended on the old state. Do not overwrite prepared inputs from raw `HEAD` or change hashes merely to bless an obsolete plan.

Keep source-transaction effects distinct from external command effects. A later isolated source transaction may fail without changing its inputs while an earlier dependency command remains applied. Report the actual completed mutations and failure boundary; do not claim whole-workflow rollback without a mechanism that provides it.

## Converge within the verification contract

When preparation is a selected verification barrier, finish the required repairs, integration seams, and final dependency/lock convergence before the gated checks. A missing prerequisite does not authorize restoring a retired backend or changing the selected architecture.

Use `$verify-strict-work` for permitted commands, batch and failure order, repair rounds, time limits, and stopping conditions. Repeat only the maintenance and repair rounds required by the task within that authority. If a round makes no progress or exposes an unresolved compatibility or ownership decision, stop dependent work and report it rather than turning convergence into an unlimited retry loop.

Planning and documentation remain in their authorized phase. This reference grants no dependency-command, integration, verification, or persistence authority; newly written tests remain unexecuted until their authorized round runs.
