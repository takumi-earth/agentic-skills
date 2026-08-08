---
name: upgrade-strict-dependencies
description: "Plan and implement dependency, manifest, patch, fork, edition, Rust-version, toolchain, runtime-version, and lockfile migrations in `strict*` ecosystem repositories. Use for Cargo or Bun dependency upgrades, workspace centralization, source provenance changes, strict-owned forks, feature migrations, compatibility floors, or template-propagated manifest changes. This skill preserves capability and exact source identity instead of downgrading or broadening scope when an upgrade breaks."
---

# Upgrade Strict Dependencies

Lock the migration matrix, preserve strict ecosystem provenance, and adapt to the selected version instead of treating breakage as permission to roll back.

When more than one dependency is being evaluated or no dependency has been selected, use `$review-strict-dependency-candidates` first. Candidate research is not manifest authority.

## Establish the upgrade matrix

Record:

- in-scope repositories and manifests, including maintained excluded members;
- package, current version/source, target version/source, and version policy;
- exact features, default-feature behavior, target conditions, and optionality;
- Rust edition, `rust-version`, toolchain, Bun/runtime, and compatibility-floor changes;
- strict-owned forks, Git revisions, branches, tags, and root patch tables;
- public API or behavior migrations required by the new version;
- lockfile, generated manifest, template, and consumer fallout;
- canonical formatting, generation, and verification commands;
- explicit exclusions, authorized forks, and forbidden adjacent upgrades.
- the approved candidate-ledger entry and user selection when the dependency is new.

Do not infer scope from whichever manifest currently fails.

## Verify versions and provenance

- Use current local checkouts beneath `~/strict-rs/*` as the first source for strict-owned crate ownership, manifests, safety policy, tests, and repository guidance.
- Use current primary sources for the latest version, features, release notes, and migration requirements.
- Preserve exact Cargo source identity: registry, Git URL, revision, branch, tag, or path.
- Do not replace a strict-owned fork with a crates.io package merely because names match.
- Do not introduce a local path dependency, new fork, or unrelated patch without authorization.
- Treat a named compatibility floor as separate from the primary supported runtime.
- For Rust, distinguish Cargo's `rust-version` from `rustup` toolchain selectors: a two-component selector tracks the newest patch in that release line, while a three-component selector pins one patch. Preserve the selected policy in CI, documentation, and verification commands instead of normalizing between them.
- Inspect consumers before changing public features or removing compatibility surfaces.

Before adding a new third-party crate, require the candidate review to cover release and maintenance health, license, edition, MSRV, platform support, default and selected feature footprint, transitive dependencies, unsafe implementation policy, advisories, supersession, and API/lifecycle ownership fit. Reconcile the living goal, record a local stop on every dependent manifest and lockfile edit, present the comparison, continue independent authorized work, and wait for explicit selection. Use `$maintain-living-goal` for a whole-goal `blocked` transition only when the same genuine impasse leaves no meaningful in-scope work and survives the harness audit.

## Centralize workspace dependencies structurally

When the workspace root owns dependency policy:

- Put shared version/source/features in `[workspace.dependencies]`.
- Use `{ workspace = true }` in member manifests.
- Preserve target-specific, optional, build, and dev dependency placement.
- Keep `[patch.*]` at the owning workspace root.
- Update every maintained manifest in scope, not only active default members.
- Let the lockfile follow the canonical Cargo workflow.

Do not centralize merely for textual uniformity when members intentionally require different sources or features. Document the semantic reason for a real difference.

Read [the dependency migration checklist](references/dependency-migration-checklist.md) for manifest-heavy work.

## Migrate forward

When the selected upgrade breaks:

1. Inspect the new API, feature, or schema surface.
2. Identify the owner of the adaptation.
3. Migrate code, configuration, generator, or harness at that owner.
4. Preserve intended product and fork capabilities.
5. Add positive and negative behavior evidence for changed behavior.
6. Converge generated and consumer surfaces.

Do not revert the upgrade, pin an older version, add a compatibility shim, remove a feature, or expand to another fork unless the user explicitly selects that outcome.

Treat “upstream does not support it” differently when the dependency is an owned fork: the fork is an authorized refactoring surface within the task scope.

## Preserve stage and policy boundaries

- An edition/dependency stage does not authorize lint-policy promotion, unrelated feature redesign, or downstream cleanup.
- A successful product build does not make ignored or excluded maintained manifests optional.
- A resolver or compile failure is diagnostic evidence, not authorization to modify sibling repositories.
- Dirty worktrees do not justify `--check` formatting, skipped generation, or reduced verification.
- Generated manifest or template changes must flow through their source owner.
- Public API, feature retirement, and compatibility changes must be explicit in an approved plan.

## Verify in the correct order

Subject to the active verification contract:

1. Run the real formatter or generation workflow after edits.
2. Resolve metadata and dependency selection at the owning workspace.
3. Exercise the primary supported runtime/version first.
4. Exercise compatibility floors or alternate configurations separately.
5. Run the repository's exact canonical gate.
6. Report lockfile and generated fallout.

Do not substitute narrower raw commands, enlarge timeouts, change acceptance policy, or call a focused diagnostic a passing upgrade gate.

## Report the migration

State:

- selected versions and exact provenance;
- manifest and feature ownership changes;
- capability/API migrations;
- maintained consumers updated;
- generated and lockfile fallout;
- primary and compatibility verification states;
- any blocker requiring a user-owned scope, fork, compatibility, or policy decision.
