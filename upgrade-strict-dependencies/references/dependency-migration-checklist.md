# Dependency migration checklist

Use the applicable rows only. Repository guidance and the live task contract take precedence.

## Inventory

- Enumerate workspace roots, members, excluded-but-maintained crates, nested workspaces, and nested product repositories.
- Record dependency occurrences across normal, dev, build, and target-specific tables.
- Record registry, Git, revision, branch, tag, path, patch, optional, feature, and default-feature fields.
- Identify generated manifests, templates, and updater-owned files.
- Identify public APIs and behavior tied to the dependency.

## Target

- Confirm the exact target version and source from a current primary source.
- Confirm edition, `rust-version`, toolchain, and runtime compatibility.
- Confirm renamed/removed features, APIs, schemas, MSRV, and lockfile format.
- Identify which strict-owned fork or workspace root owns adaptation.
- Record explicit non-goals and unauthorized adjacent forks.

## Edit

- Centralize shared policy at `[workspace.dependencies]` when semantically shared.
- Preserve target conditions, optionality, feature sets, and source identity.
- Keep patches at the owning root.
- Update generators/templates before generated consumers.
- Migrate code and behavior forward; do not downgrade or shim by default.
- Preserve public capability unless breakage is explicitly selected.

## Evidence

- Add positive and negative behavior tests at the owner boundary.
- Run authorized formatting and generation workflows.
- Test the primary runtime/version before compatibility floors.
- Run the exact canonical gate.
- Report focused diagnostic results separately from acceptance.
- Review lockfile and generated fallout without reverting unrelated user work.

## Stop gates

Stop before:

- changing a strict fork to crates.io or a different Git source;
- adding a local path or new patch/fork;
- retiring a public feature or compatibility surface;
- expanding into an adjacent repository or rollout stage;
- changing lint, coverage, mutation, timeout, or canonical-command policy;
- reverting the selected upgrade because its migration requires design work.
