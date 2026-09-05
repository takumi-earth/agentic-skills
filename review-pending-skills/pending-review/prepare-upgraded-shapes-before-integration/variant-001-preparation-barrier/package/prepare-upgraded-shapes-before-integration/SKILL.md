---
name: prepare-upgraded-shapes-before-integration
description: "Order integration against upgraded and repaired dependency shapes, with dependency tools owning resolution and fresh inputs preceding source planning. Use when an integration workflow includes toolchain or dependency preparation; not for routine lock maintenance or an integration with no preparation dependency."
---

# Prepare Upgraded Shapes Before Integration

Write integration seams for the selected upgraded target, not the unprepared checkout. Preserve the dependency between preparation, compatibility repairs, integration, and verification.

## Establish the required predecessor state

Read the user's target policy, supported build surface, and public workflow boundary. Distinguish current source shape from the state the integration is required to consume. If preparation belongs to the first public `apply`, do not silently move it into an unrelated manual prerequisite.

Preserve this order where those stages are required:

```text
toolchain/edition alignment
    → dependency requirements and graph resolution
    → upgrade-related compatibility repairs
    → integration seams against repaired shapes
    → final dependency/lock convergence
    → verification
```

Assign each repair its actual prerequisite. An existing phase name or stage list cannot justify running a seam before the repair whose shape it consumes.

## Let the dependency tool own maintenance

Invoke the selected dependency manager through the authorized orchestration boundary. Deterministic repair jobs own explicit source/configuration transformations; they do not implement dependency resolution, hand-edit lock graphs, or infer source migrations by parsing live diagnostics.

For a Cargo workflow whose policy requires latest incompatible and pinned-requirement upgrades, preserve its selected commands, such as `cargo upgrade --recursive --incompatible --pinned` and `cargo update --recursive`. Do not substitute conservative `cargo update --workspace`, an old dependency pin, or a home-grown resolver. Repeat the required maintenance/repair rounds until the selected target converges, within the granted authority.

Do not import those commands into a workflow with a different selected policy or add excluded build-system maintenance merely because related files exist.

## Refresh authority after real effects

After an external mutation, reload the resulting manifests, lock state, and relevant source before dependent planning. Refresh semantic indexes and preconditions from that state. Do not carry stale captures forward, overwrite preparation from raw `HEAD`, or change hashes merely to bless an obsolete plan.

Keep inventory transactions and external command effects distinct. A failed isolated source transaction may leave its authoritative inputs unchanged; that does not mean an earlier dependency command was rolled back. Report completed mutations and failures accurately. Do not promise whole-workflow atomicity unless the real workflow supplies it.

## Enforce the verification boundary

When preparation is a user-required barrier, do not run checks, Clippy, tests, or selected nextest before preparation, repairs, seams, and final convergence. Do not enable a retired backend to make those gates run.

When the user requires complete verification iterations, run every applicable command once, adjudicate all issues together, and implement the complete structural repair round before any rerun. Record a command blocked by a genuine prerequisite without manufacturing a passing result or weakening the architecture. Newly written tests remain unexecuted evidence until their authorized round runs.

This skill defines ordering, not permission to run dependency commands, integration, verification, or installation. A documentation or planning request stays in that phase.
