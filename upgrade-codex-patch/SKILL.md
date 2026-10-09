---
name: upgrade-codex-patch
description: Refresh canonical `agentic-skills`, rebase and audit a versioned Codex patch, prepare a complete platform package, and publish the successor with a user-run runtime handoff. Execute the final `just i` handoff only when explicitly requested. Use for carried Codex release patches or this package's source installation workflow, not general Rust dependency modernization or read-only patch inspection.
---

# Upgrade Codex Patch

Carry the previous release patch forward without losing upstream behavior, then prove the provenance of every difference in the successor patch.

For source installation or launcher preparation without a release-patch upgrade, read [complete source-package installation](references/installation.md) and use the imported `just i` recipe. Default to package preparation and return the final command for the user. Run the runtime-replacing handoff only when the user explicitly asks to execute it. The patch-rebase, dependency-upgrade, export and publication steps below belong to the release-upgrade mode; an installation-only request does not authorize those effects.

## Reserve the final handoff for the user

A skill invocation or a request to finish an upgrade authorizes preparation, validation, artifact retention, and this repository's publication workflow. It does not authorize choosing when to stop or restart the user's live Codex processes. Prepare the complete package with `just i --prepare-package`, finish the audit and publication, then stop and report readiness with the exact returned handoff command. The user chooses when to run it. Do not execute that command, launch a delayed or detached replacement, use `--no-daemon` to publish live aliases as a preparation substitute, or restart services unless the user explicitly requests that handoff. Isolated installer fixtures retain their separate verification scope.

## Repair the supported workflow at its owner

- A reported failure leaves the authorized workflow unfinished. Diagnose and repair the normal entrypoint until it performs its intended installation and runtime replacement. Manual recovery, matching version strings, and a successful receipt from an already-repaired environment do not establish that a subsequent upgrade will work.
- Trace the existing build, package selection, process shutdown, startup, and helper ownership before choosing an implementation. Installation orchestration belongs in this package's installer. Use existing native lifecycle commands before proposing additional Codex runtime APIs, process-admission policy, or source patches. Add a Codex source change only when a concrete requirement cannot be met at the installer owner; explain that necessity before expanding the carried patch.
- Treat replacement as an external handoff: prepare and validate the complete new package first, stop the old runtime and its helpers, prove they exited, select and pin the new package, and start it with the user's saved settings. The handoff must survive termination of the session that initiated it. Keep progress and a durable outcome available after reconnecting.
- Write the implementation for macOS, Linux, and Windows. Keep platform process operations in the installer; do not turn one host's API into a shared assumption. Native verification on the other platforms may occur in the user's respective sessions.
- Verify an upgrade from an older running package, including the reported missing-registration state, through the supported `just i` entrypoint. Verify old process exit and new executable/package provenance as well as version readback. Keep build failure before shutdown and unrelated-process preservation covered. Do not call the repair resolved from mocks, manual kills, `/daemon`, or a same-version checkpoint alone.
- Continue remediation within existing authority. Ask only when a concrete necessary effect conflicts with another instruction. Preserve the Codex command restrictions below; installer tests and skill validation do not authorize Codex tests or extra Cargo commands.

## Refresh the canonical skill repository at launch

- Read [the repository lifecycle](references/repository-lifecycle.md) before changing the Codex checkout. Use `$manage-agentic-skills-repo` to pull the canonical `agentic-skills` source and integrate incoming commits under its standing authorization and preservation rules. Complete that refresh before patch application or Cargo; do not add a separate fast-forward-only restriction or Git permission request.
- After any incoming update, reload the refreshed canonical `AGENTS.md`, this `SKILL.md`, and required resources through EOF before proceeding. Use that package's scripts and `assets/patches/`; a stale installed copy must not govern the run. Reuse a successful refresh within the same invocation rather than recursively restarting it after reload.
- Honor an explicitly selected predecessor. Otherwise compare the applicable versioned patches in the refreshed package's `assets/patches/` and the local artifact directory, using release order and the verified target base. Resolve different bytes for the same release before applying anything. Packaged patches make the lineage available on another machine without the original local artifact directory.
- An explicit artifact selection is already the resolution of differing copies. Use that exact patch; do not import changes from a stale alternate copy or ask the user to select it again.

## Preserve the execution contract

- Resolve the Git top-level, target Codex release and base commit, previous patch path, successor patch path, and Cargo workspace directory before mutating the Codex checkout. When paths are implicit, use the verified checkout release and applicable packaged or local versioned predecessor; resolve material ambiguity before applying a patch.
- Read all applicable `AGENTS.md` files. This workflow's explicit command contract supersedes repository guidance that would otherwise require formatting, fixing, tests, Clippy, generators, or other repository commands outside patch mechanics, the initial Cargo sequence and the supported `just i` installation path.
- In the Codex release-upgrade lane, do not run or ask to run `just fmt`, `just fix`, tests, Clippy, `just bazel-lock-update`, other generators, or substitute repository commands. Do not treat their omission as a blocker. A future explicit user instruction may change the contract, but the skill must never solicit that expansion. Separately authorized maintenance of canonical skill guidance follows that repository's validation and Git workflow; it does not expand the Codex command surface.
- The Codex checkout permits patch inspection, application, source remediation, comparison, successor-artifact operations, the four initial Cargo commands below, and the package's `just i` preparation/installation workflow. Its base commit, staged work, and history remain protected. Normal Git index-cache refreshes are permitted; protect staged entries and the staged/unstaged split, not the serialized cache bytes. Separately, this workflow refreshes the canonical `agentic-skills` repository, retains the audited patch there, and stages, commits, and pushes all of that repository's changes to its verified canonical upstream. These lifecycle effects do not authorize switching the Codex base, changing its staged work or history, Codex fetches or pushes, or unrelated cleanup.
- Keep the previous patch immutable. Record its SHA-256 digest, byte size, line count, and changed-path inventory.
- Inspect the worktree and index before applying the patch. Preserve unrelated user changes and exclude them from the successor patch.
- Read [the patch selection contract](references/patch-selection.md) before preparing an export. Select intentional changes by Cargo field or source hunk, not by whole-file inclusion. Retain resolver changes, introduced/changed/removed pins, genuine dependency additions/removals, required non-version manifest changes, and reviewed source fixes. Exclude ordinary version bumps of existing dependencies and `codex-rs/Cargo.lock`, including minimum-version bumps supporting source/API migrations; the required `cargo upgrade` and `cargo update` rounds cover them in the live worktree.
- Read [the audit helper workflow](references/audit-helper.md) and use `scripts/audit_upgrade.py` to persist a pre-application snapshot, compare command fallout, and audit the final artifact. Record additional intended paths explicitly; preserve an existing successor unless it is an artifact created by this run.
- Do not use `git apply --3way`: it can change the index. Do not stage or unstage files to manufacture a clean patch.
- Do not delegate unless the user explicitly requests agents or parallel work.

## Rebase the previous patch

Run patch commands from the Git top-level so paths such as `codex-rs/...` resolve correctly.

1. Run `git apply --check --verbose <previous-patch>` and retain the complete diagnostics.
2. If the check succeeds, run `git apply <previous-patch>` once.
3. If the check fails, distinguish context drift from changed upstream behavior before editing:
   - Read each failed patch hunk and the complete affected owner file.
   - Compare the old release base, new release base, and patch intent.
   - Preserve both the carried behavior and compatible behavior added upstream.
   - Stop for direction if the old behavior has no unambiguous owner or conflicts materially with the new design.
4. After classifying every failure, run `git apply --reject <previous-patch>` only when the target paths contain no conflicting user work. Treat each generated `.rej` file as a transient list of unapplied hunks.
5. Remediate every reject directly in its owning source file. Account for all cleanly applied and manually ported hunks, then remove only the generated `.rej` files after their content is represented in source.
6. Generate a candidate patch and compare it with the previous patch using `scripts/compare_patch_hunks.py`. Inspect every non-identical carried hunk; never infer equivalence from line numbers, `interdiff` placement, or command silence.
7. Apply any explicit release-specific additions requested by the user, such as a crate-level recursion limit, and identify them separately from carried hunks.

## Prepare the launcher and run the initial Cargo sequence

Read [complete source-package installation](references/installation.md) when installing or preparing the V8 launcher. Use the skill's imported `justfile`; resolve `AGENTIC_SKILLS_REPO`, the selected Codex checkout and `CODEX_V8_REPO` before execution. Run `just i --prepare-v8` before Cargo so the native wrapper exists on this platform. This preparation uses compatible Bun from the selected runtime, not a machine-specific path in shared Cargo configuration.

Run the initial sequence from `codex-rs` in exactly this order:

```bash
cargo upgrade --recursive --verbose
cargo update --recursive
cargo install --path cli
cargo install --path code-mode-host
```

- Keep this initial order. The additional supported steps are V8 preparation and complete installation through `just i`; repository guidance cannot add a formatter, fixer, test, lint, generator, or lockfile-maintenance command.
- With the current crate layout, `cargo install --path cli` installs both `codex` and `logs_client`; `cargo install --path code-mode-host` installs `codex-code-mode-host`. Confirm all three from successful Cargo installation output. Check the relevant manifests and installation output before interpreting a missing-component question as a need for another install command.
- Do not add `--incompatible`, `--pinned`, alternate feature flags, cache redirects, or substitute commands unless the user requests them.
- Let Rust commands wait for Cargo locks. Do not kill them merely because compilation is quiet or slow.
- Retain each command's complete stdout, stderr, exit status, and duration. At the harness's required reporting cadence, give the elapsed time and latest observed stage; use a brief waiting update while quiet and fuller updates for stage changes, failures, remediations, or completion. Silence alone does not identify a compilation or linking stage.
- If a command fails because of permissions, sandboxing, cache access, temporary-directory access, or network restrictions, rerun the same command through the harness escalation mechanism. Do not change the command's behavior to evade the restriction.
- After each Cargo command, take another helper snapshot and compare it with the immediately preceding snapshot. Classify manifest and lockfile changes separately from source changes or pre-existing work. Do not invoke an extra repository mutator to reconcile them.
- Keep the pre-Cargo curated selection independent of these snapshots. Review any build remediation at field/hunk granularity; automatic manifest bumps are not additions to patch intent.

Cargo installs produce loose binaries. After they succeed, run `just i --prepare-package` with the three prebuilt-binary arguments in [the installation reference](references/installation.md). It uses the official platform package builder and retains `logs_client`, leaving live aliases, package selection, and running services untouched. Record the prepared package and its exact returned handoff command. Publish the audited patch and guidance, then report ready for the user to run that command. Do not claim live installation from Cargo or package preparation. Direct `just i` does not itself upgrade dependencies, apply/export patches, or grant Git authority.

The default `just i` entrypoint owns an independent installer lifetime and durable outcome capture, including when it replaces the invoking agent's daemon. Read the installation reference's recovery procedure before the handoff. After reconnecting, inspect that original invocation and receipt before retrying. Distinguish installed versions, process and package provenance, shared feature compatibility, client attachment, and model-visible tools in the report.

## Remediate build failures

Trace each build failure to the dependency and API boundary that introduced it before choosing a remedy.

- Use contained code adaptation when the required change is small, cohesive, and owned by a limited number of files or call sites. Preserve upstream behavior and platform support.
- Pin the responsible dependency to a known working version when adapting it would require large, cross-crate, generated, protocol-wide, or otherwise wide-reaching changes.
- Establish a pin from concrete evidence such as the previous lockfile, previous manifest, or a version that built successfully. Do not guess a version or downgrade unrelated dependencies.
- Express a stability pin exactly when Cargo must not float to a newer compatible release. For remediation retries, rerun only necessary commands from the same allowlist: use `cargo update --recursive` when resolution must change, then rerun the failed install command (`cargo install --path cli` or `cargo install --path code-mode-host`). Report retries separately from the initial sequence.
- Repeat diagnosis and the smallest necessary remediation until both installations succeed or a material unresolved choice requires the user.
- Keep the same initial Cargo sequence and supported `just i` installation path during remediation. Do not run or request formatters, fixers, tests, Clippy, Bazel commands, or generators as supporting evidence.

## Produce the successor patch

1. Build the selected change units from carried intent, contained source remediation, deliberate pin changes, genuine dependency additions/removals, non-version manifest changes and explicit additions. Use the user's staged/unstaged split as selection evidence when they designate it; preserve that split. A path inventory bounds the audit but cannot select hunks within a file. Account for new files explicitly.
2. Prepare and freeze the reviewed hunk/field export against the verified target `HEAD` as described in the selection contract. Generate the candidate from that curated selection. Do not export whole live-file diffs, include ordinary version bumps of existing dependencies, mutate an index to obtain an export, or omit authorized untracked source. Preserve the predecessor's original bytes; a requested same-release revision uses a separate candidate before replacing its selected destination.
3. Run the helper's final audit with the frozen `--selected-export` and an external `--scratch-root`. Require unchanged predecessor bytes, `HEAD`, and staged index entries; preserved unrelated edits and the staging split; intended paths; exact equality with the reviewed export; and applicability against a private filesystem view of the target base. A non-pristine index skips only the additional cached check. Allow Git to refresh cached filesystem metadata; raw `.git/index` byte changes do not require an exception and are not an audit failure. The helper never stages or unstages work, and ordinary version changes in the live checkout cannot force a broader export.
4. Compare the previous and successor patches with `scripts/compare_patch_hunks.py` and classify every difference as one of:
   - byte-identical carried edit;
   - upstream-aware semantic rebase;
   - intentional dependency/manifest change, excluding ordinary upgrade and lockfile fallout;
   - contained build remediation;
   - dependency pin;
   - explicit release-specific addition.
5. After the audit and complete package preparation pass, follow [the repository lifecycle](references/repository-lifecycle.md) to retain a byte-identical versioned copy in `upgrade-codex-patch/assets/patches/`, keeping the local successor as well. Then stage, commit, and push everything in the canonical `agentic-skills` repository, including pre-existing changes and deletions. Require verified upstream publication before reporting the upgrade ready for its user-run handoff.
6. Report the target release and base commit; local and packaged successor paths, SHA-256, byte size, line count, path count, and hunk count; comparison classifications and separate applicability results; successful Cargo build/install results and the prepared package; retained or new pins; excluded command fallout; Codex index/worktree disposition; repository refresh result; and the `agentic-skills` commit hash, scope, push destination and result, and remaining unpublished commits. Include the exact final handoff command and identify live activation as reserved for the user. Use the helper's workspace-aware pin records instead of assuming which manifest owns a version.
7. Report the initial four Cargo commands, V8 preparation, and complete package preparation separately. Report native daemon selection, restart, and live verification only when an explicitly requested handoff was actually executed. Do not ask permission for omitted repository commands or present their omission as incomplete verification.
8. Leave the Codex worktree unstaged and uncommitted unless the user separately authorizes those effects. The required final commit belongs to `agentic-skills`.

## Patch comparison helper

Use `scripts/compare_patch_hunks.py` for Git-style unified patches. It ignores index hashes, hunk offsets, and unchanged context; compares ordered added and removed lines; aligns identical hunk edit streams; reports new and removed file sections; and renders normalized diffs for changed edit streams. Its equality result proves identical added/removed lines, not byte-identical complete patch files. Use `--summary` only when exact differing lines are not needed.
