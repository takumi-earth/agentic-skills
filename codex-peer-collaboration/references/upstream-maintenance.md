# Upstream maintenance strategy

Recorded: `2026-10-02`, `Asia/Hong_Kong`.

Last materially updated: `2026-10-09`, `Asia/Hong_Kong`.

The user requested the minimum practical overhead for pulling newer upstream Codex changes and applying this feature. On `2026-10-09`, the user explicitly selected the five requirements in this reference and requested their incorporation by the existing `codex-bun` peer alongside its reusable integration work. The shared-fork, runtime-owned architecture remains selected. Semantic peer integration, a CI pipeline, and a new updater remain unimplemented; selected requirements are separate from evidence of implementation. [The maintained plan](plan.md#codex-bun-peer-handoff-and-consumer-lane) owns the concrete peer handoff and current disposition.

## Optimize the recurring work

Separate three costs:

- **Porting:** rediscovering owners, repairing patch context, and adapting actual upstream API changes.
- **Validation:** establishing that the intended lifecycle, tool registration, approval policy, and delivery still work.
- **Building and deployment:** producing matching platform packages and activating the selected runtime.

The intended routine update has zero manual source porting when upstream preserves the relevant interfaces. Real incompatible API or ownership changes still require a focused repair. Do not promise that every upstream revision can be accepted automatically.

## Keep product code owned and the upstream seam small

Put the registry, message protocol, delivery state, authenticated cross-host connection, and peer policy in one focused runtime component with its own modules and behavior tests. Initialize it with the app-server's lifetime and preserve runtime ownership; an internal adapter must not transfer ownership to an independently configured external peer service.

The candidate upstream integration families are:

| Integration family | Intended delta |
| --- | --- |
| Workspace/build membership | Include the owned peer component and required platform build inputs |
| Runtime construction and lifetime | Create/connect the peer component at the app-server-owned lifecycle boundary |
| Model tool contribution | Expose peer operations consistently to desktop, TUI, and phone-controlled sessions |
| Configuration/protocol projection | Carry the peer policy, host/session identities, and delivery results through their proper owners |

These are candidate integration families, not a verified file or edit count. Choose the actual seams after reading their owners and checking available factories/contribution interfaces. Measure the number of upstream-owned interfaces depended on and how frequently their contracts change. A small edit inside a frequently rewritten upstream function can cost more to maintain than a larger owned component.

Prefer a narrow existing extension/factory seam when it preserves the architecture. Keep necessary adaptations in small typed adapters. Avoid copying complete upstream algorithms, scattering peer logic through large core/TUI modules, or broadening subagent-tree authority to reduce diff size.

Keep one portable peer implementation for Mac and Ubuntu. Put genuine platform differences in the owned component or packaging. Existing network/toolchain/wrapper patch families need their own dispositions; they are not automatically portable merely because the new peer feature is.

## Automate the integration delta semantically

Use `$design-semantic-source-transforms` for the integration declarations and `$test-adaptive-source-transforms` for their behavior evidence.

Each declaration needs a stable identity, semantic owner, complete permitted search scope, resolved query, relevant precondition, minimal rewrite, semantic postcondition, and required cardinality.

For example, discover the app-server lifecycle constructor and tool-contribution owner by their load-bearing types/relationships, then add the owned peer contribution and verify that it is registered exactly once. Preserve unrelated initialization, fields, instrumentation, and upstream behavior. Formatting, line shifts, unrelated fields, and file movement must not require manual porting. A genuine incompatibility must identify the affected integration point and the actual failed semantic condition.

Paths and prior source locations may accelerate discovery; they must not decide identity or suppress the full query. Do not use complete-body replacements, exact source fragments, token fingerprints, regex matching, first-match mutation, or package-version gates as adaptive target identity.

Use typed syntax where it establishes identity across the complete scope; add symbol resolution when aliases, traits, receiver types, or method resolution make it necessary. This avoids paying for an unnecessarily broad semantic index while preserving the required discovery contract.

The semantic layer must distinguish application, recognized post-state, required absence, optional absence, ambiguity, mixed state, incompatible shape, failed postcondition, and non-idempotent replay. Plan against a virtual transaction; publish only after the postcondition passes and replay produces no semantic delta. Failed classification or validation leaves authoritative source unchanged.

Exact copying of the peer component's entirely owned files can be an ownership-specific operation. Keep that distinct from adaptive edits inside upstream-owned source.

## Reuse existing integration infrastructure carefully

The complete README and applicable root guidance were inspected in `~/rust-forks/codex/codex-rs/bun` at the original documentation checkpoint. Its README describes the existing `patch-engine/` primitives for `VirtualRoot`, Rust Analyzer indexing, typed `FileEdit` ownership, phase planning, atomic publication, and replay checks. On `2026-10-09`, the user confirmed that the existing `codex-bun` peer already has reusable application infrastructure without patch files.

Have that peer assess and incorporate the peer consumer through the actual owners before building another generic engine. Its existing machinery is the first reuse candidate; compatibility with these peer declarations still needs a concrete owner/capability mapping and behavioral evidence. Record reusable operations, genuine gaps, permitted source scopes, typed outcomes, publication boundaries, and replay results. Documentation and the existence of an engine do not establish peer declaration fitness.

Keep upgrade-time machinery out of the shipped peer runtime's dependency graph. Reusing an indexing/planning component does not select Bun as this feature's execution backend.

The public Bun `apply` workflow also changes toolchains/dependencies, repairs source, installs integration seams, and enforces its Bun execution contract. Select bounded peer-only reuse through the actual owner without importing those broader effects. The peer's already-authorized full Bun work keeps its own scope and ordering; this consumer request does not bypass that workflow's ownership rules or verification gates.

## Proposed routine update

1. Resolve one immutable upstream commit/tag for the run. Keep source provenance consistent across the Mac and Ubuntu package builds.
2. Prepare the target under the authorized upgrade workflow. The current Codex checkout's `HEAD`, index, and history remain protected; a separate target workspace is a workflow choice requiring authority, not an implicit exception.
3. Materialize the owned peer source and evaluate the small integration declarations against the complete declared scopes.
4. Classify, plan, verify semantic postconditions, and replay before publishing the owned source changes. Stop for genuine interface/ownership incompatibility with a precise report.
5. Run the current authorized dependency/build sequence, refreshing source/resolution snapshots and semantic indexes after Cargo effects. Do not claim that a virtual source transaction rolls back external Cargo writes.
6. Stage matching runtime packages from the successful built artifacts when packaging is authorized. Reuse package-builder prebuilt inputs to avoid a second compilation for assembly.
7. Export, audit, and retain the immutable successor patch and package provenance. Explicitly account for new owned files; `git diff HEAD` alone omits untracked files.
8. Activate the selected packages and verify client attachment only within activation authority.

The current upgrade workflow assumes the target Codex release/base was selected separately and does not authorize Codex fetches or base switching. A future single-command updater needs an explicitly defined source-fetch/target-preparation lane, preferably isolated from the user's working checkout. Do not silently turn the current patch workflow into `git pull` or a rebase of that checkout.

The selected production design applies owned code and semantic declarations without patch-file input, then produces a versioned Git patch as a reproducible release/provenance/audit artifact for the accepted upstream base. Preserve predecessor artifacts and the existing provenance/audit checks. A patch file is not a fallback for a failed semantic target query. The user has authorized the existing peer to incorporate this capability into its reusable work; adapting the release-upgrade owner remains a separately scoped effect rather than an implicit change to its active commands.

Use the complete current `$upgrade-codex-patch` contract for each authorized release/build/install run instead of freezing an old command list in this reference. Preserve its exact dependency/build/package sequence, base/staged-entry/history protections, audit requirements, command lifetime, and recovery rules. The selected production design keeps artifact generation after semantic application and validation, and activation within the authority of the invoking workflow. Do not add tests, generators, substitute build commands, source fetches, or activation effects to an invocation merely because this design mentions them.

## Build and release overhead

- Preserve normal Cargo caches and stable build inputs where practical; do not clean caches as routine upgrade preparation or redirect them to bypass restrictions.
- Recognize that changed upstream workspace versions, dependencies, toolchains, or build inputs can still cause substantial rebuilds.
- Produce each platform package once per accepted build revision, with source/patch provenance, target, toolchain/resolution information, and artifact identity. Reusing already built packages for installation avoids compiling again on every consuming machine.
- A future CI build/cache/distribution lane can automate platform builds, but it is a separate proposed workflow. The current user's source-build capability remains supported.
- Dependency refresh required by the active upgrade workflow can add rebuild cost. Changing its frequency or build profile is a separate workflow decision; semantic porting automation does not silently make that change.

## Evidence and long-term reduction

When transform implementation is authorized, prove movement/reordering, unrelated extension, aliases where relevant, near-match decoys, genuine ambiguity, real semantic drift, recognized post-state, and replay through typed outcomes. Add owner-level behavior evidence for the actual peer lifecycle and message authority; textual patch application or compilation alone is insufficient.

Use authorized behavioral evidence at the correct phase. Do not add unrequested tests or generators to the restricted release-upgrade sequence.

Track the inventory of upstream-owned integration points and their reasons for changing. Repair only the affected adapters/declarations after actual incompatible drift rather than repeating the full investigation.

The largest long-term reduction would be upstream acceptance of suitable extension points, or the peer capability itself. That is an optional contribution direction; no upstream communication or publication is authorized by this reference.
