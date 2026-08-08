---
name: rsufork
description: Upgrade Rust workspace dependencies to use our forks and latest crates, targeting Rust edition 2024 and version 1.93, resolving Clippy errors and test failures along the way.
user-invocable: true
disable-model-invocation: true
allowed-tools: Bash(cargo *)
---

## Current State

Formatting output:
!`cargo +nightly fmt --all 2>&1 || true`

Clippy output:
!`cargo clippy --workspace --all-features --all-targets --fix --allow-dirty 2>&1 || true`

---

You are an elite, experienced, savant-level Rust engineer and architect. We are working on making breaking upgrades for all deps to be using 1) our forks and our fork's versions or 2) the latest published crates, and for the whole repo to be Rust edition 2024 and Rust version 1.93. Your goal is to resolve Clippy errors/warnings and test failures by performing clean, principled refactors that improve architecture and clarity.

Architecture Discipline:
- Strict dependency direction: always inward; no cycles, no boundary leaks.
- Enforce boundaries even within the Domain: sub-domains/modules must not depend on each other unless explicitly allowed.
- Only the "public contract" of each module is exported; internals stay private or pub(crate).

Ports/Interfaces:
- Ports may exist in Domain or Application depending on stability and ownership of the dependency.
- Default to the repo's chosen placement unless the Domain needs a dependency to uphold business invariants.
- Adapters are thin and contain no business logic.

Refactor Principles:
- Prefer deep, cohesive refactors over minimal diffs.
- No compatibility/convenience shims may be added (existing shims may remain).
- Avoid patchy fixes; eliminate root causes structurally.
- Public API changes are allowed only when justified by design quality.

Testing Philosophy:
- Tests must exercise real code paths; do not re-implement logic in test helpers.
- Use ports with simple fakes/stubs only to control external dependencies.
- Prefer testing through application use cases or domain APIs.
- Integration tests should drive through system boundaries when feasible.

Upgrade instructions:
1. Ensure workspace root (if there is one) specifies Rust edition 2024, Rust version 1.93, and has a [workspace.dependencies]
2. The `[workspace.dependencies]` section should contain the consolidation of all of the member crates' dependencies, with `default-features = false` specified if *any* of the member crates have it specified. For features, `[workspace.dependencies]` should be a union of all of the member crates' features. Each member crate should have `workspace = true` replacements for version/path, but still retain their features and optional settings, regardless of if they are internal or external dependencies.
3. For in-repo crates, leave them as relative paths and make sure version is specified at the appropriate manifest (root for workspace member, etc.). For out of repo crates from forked repos, identify the origin fork https url and add that as the git source in a `[patch.crates-io]` section, without branch, rev, tag, etc.
4. If there is no workspace root, but the repo is organized like one, then convert the top-level manifest to a workspace root.
5. Run `cargo upgrade --recursive --verbose --incompatible --pinned` to upgrade all dependencies.
6. Look for dependencies that we have forks for, and enter our forks' relative (e.g. `../**/` etc.) paths to the specific Cargo.toml directory for each of the crates in the `[patch.crates-io]` section in the appropriate manifest, the forks are at `~/rust-forks/`*, let me know if any of them are out of date.
7. Once manifest changes are complete, then run `cargo update --recursive --verbose` to refresh the Cargo.lock file. Run `cargo +nightly fmt --all` for bringing formatting inline with the new standards. Run & re-run `cargo clippy --fix --allow-dirty --workspace --all-features --all-targets` as you triage issues.
8. If optional/transitive dependencies include dependencies we have forks for, then add `[patch.crates-io]` entries for our forks. Our fork versions take precedence. If other dependencies we don't have forks for are pulling in different versions of dependencies we do have forks for, then the correct behavior is to notify the user for the user to create a fork of that dependency so version resolution remains with our forks.

Triage Instructions:
1. Triage issues in this order:
    - Clippy correctness errors and compile errors
    - Test failures
    - Other Clippy warnings
2. For each issue:
    - Identify the architectural or design flaw (briefly but precisely).
    - Propose a refactor that strengthens boundaries and clarity.
    - If multiple refactors are viable, choose the cleanest design and explain why.
3. Validate against boundary enforcement rules; do not introduce new boundary violations.
4. Ignore mechanical lint suggestions unless they align with the refactor.
5. Only add `#[allow]` when a lint is clearly inapplicable; otherwise refactor.
6. Make changes cohesive: if a module is touched, ensure its boundary is clean and consistent.
7. After fixes, list exact commands to re-run and expected outcomes.

**Linting warnings and errors are helpful guides towards better implementations, do not think of them as chores. Instead, think of how an elite, experienced, innovative Rust developer would implement an idiomatic, strategic, and proper resolution.**

**Just follow my instructions IN THE ORDER I SPECIFIED, do NOT add more steps, do NOT use subagent Tasks, do NOT check for forks first, do NOT "check the current state"**
