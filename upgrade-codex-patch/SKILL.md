---
name: upgrade-codex-patch
description: Refresh the canonical `agentic-skills` repository, rebase a versioned Codex Git patch onto a newer release, run the exact dependency and installation Cargo sequence, audit and retain the successor in skill resources, and commit and push all `agentic-skills` changes. Use when carrying a patch such as `~/rust-forks/codex-v0.147.0.patch` to a newer release checkout. Do not use for general Rust dependency modernization without a carried Codex patch or for read-only patch inspection that does not execute the upgrade workflow.
---

# Upgrade Codex Patch

Carry the previous release patch forward without losing upstream behavior, then prove the provenance of every difference in the successor patch.

## Refresh the canonical skill repository at launch

- Read [the repository lifecycle](references/repository-lifecycle.md) before changing the Codex checkout. Every upgrade invocation must resolve the canonical `agentic-skills` source, fetch its configured canonical upstream, and incorporate incoming commits with a fast-forward only. Preserve local commits and worktree/index changes; a failed fetch, divergent history, or an obstructed fast-forward stops the upgrade before patch application or Cargo.
- After any incoming update, reload the refreshed canonical `AGENTS.md`, this `SKILL.md`, and required resources through EOF before proceeding. Use that package's scripts and `assets/patches/`; a stale installed copy must not govern the run. Reuse a successful refresh within the same invocation rather than recursively restarting it after reload.
- Honor an explicitly selected predecessor. Otherwise compare the applicable versioned patches in the refreshed package's `assets/patches/` and the local artifact directory, using release order and the verified target base. Resolve different bytes for the same release before applying anything. Packaged patches make the lineage available on another machine without the original local artifact directory.

## Preserve the execution contract

- Resolve the Git top-level, target Codex release and base commit, previous patch path, successor patch path, and Cargo workspace directory before mutating the Codex checkout. When paths are implicit, use the verified checkout release and applicable packaged or local versioned predecessor; resolve material ambiguity before applying a patch.
- Read all applicable `AGENTS.md` files. This workflow's explicit command contract supersedes repository guidance that would otherwise require formatting, fixing, tests, Clippy, generators, or other repository commands outside the patch mechanics and four-command Cargo sequence below.
- Do not run or ask to run `just fmt`, `just fix`, tests, Clippy, `just bazel-lock-update`, other generators, or substitute repository commands. Do not treat their omission as a blocker. A future explicit user instruction may change the contract, but the skill must never solicit that expansion.
- The Codex checkout permits patch inspection, application, source remediation, comparison, successor-artifact operations, and only the four Cargo commands listed below. Its base commit, index, and history remain protected. Separately, this workflow refreshes the canonical `agentic-skills` repository, retains the audited patch there, and stages, commits, and pushes all of that repository's changes to its verified canonical upstream. These lifecycle effects do not authorize switching the Codex base, mutating its index or history, Codex fetches or pushes, or unrelated cleanup.
- Keep the previous patch immutable. Record its SHA-256 digest, byte size, line count, and changed-path inventory.
- Inspect the worktree and index before applying the patch. Preserve unrelated user changes and exclude them from the successor patch.
- Record the artifact's included and excluded paths during preflight. This versioned Codex patch lineage excludes `codex-rs/Cargo.lock`; preserve that boundary unless the user explicitly changes it. Cargo may update the lockfile in the worktree without adding it to the successor artifact.
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

## Run the only authorized build commands in order

Run the initial sequence from `codex-rs` in exactly this order:

```bash
cargo upgrade --recursive --verbose
cargo update --recursive
cargo install --path cli
cargo install --path code-mode-host
```

- Treat these commands as a complete build-command allowlist, not the start of a broader repository workflow. Repository guidance cannot add a formatter, fixer, test, lint, generator, lockfile-maintenance, or substitute command.
- With the current crate layout, `cargo install --path cli` installs both `codex` and `logs_client`; `cargo install --path code-mode-host` installs `codex-code-mode-host`. Confirm all three from successful Cargo installation output. Check the relevant manifests and installation output before interpreting a missing-component question as a need for another install command.
- Do not add `--incompatible`, `--pinned`, alternate feature flags, cache redirects, or substitute commands unless the user requests them.
- Let Rust commands wait for Cargo locks. Do not kill them merely because compilation is quiet or slow.
- Retain each command's complete stdout, stderr, exit status, and duration. At the harness's required reporting cadence, give the elapsed time and latest observed stage; use a brief waiting update while quiet and fuller updates for stage changes, failures, remediations, or completion. Silence alone does not identify a compilation or linking stage.
- If a command fails because of permissions, sandboxing, cache access, temporary-directory access, or network restrictions, rerun the same command through the harness escalation mechanism. Do not change the command's behavior to evade the restriction.
- After each Cargo command, take another helper snapshot and compare it with the immediately preceding snapshot. Classify manifest and lockfile changes separately from source changes or pre-existing work. Do not invoke an extra repository mutator to reconcile them.

## Remediate build failures

Trace each build failure to the dependency and API boundary that introduced it before choosing a remedy.

- Use contained code adaptation when the required change is small, cohesive, and owned by a limited number of files or call sites. Preserve upstream behavior and platform support.
- Pin the responsible dependency to a known working version when adapting it would require large, cross-crate, generated, protocol-wide, or otherwise wide-reaching changes.
- Establish a pin from concrete evidence such as the previous lockfile, previous manifest, or a version that built successfully. Do not guess a version or downgrade unrelated dependencies.
- Express a stability pin exactly when Cargo must not float to a newer compatible release. For remediation retries, rerun only necessary commands from the same allowlist: use `cargo update --recursive` when resolution must change, then rerun the failed install command (`cargo install --path cli` or `cargo install --path code-mode-host`). Report retries separately from the initial sequence.
- Repeat diagnosis and the smallest necessary remediation until both installations succeed or a material unresolved choice requires the user.
- Keep the same command allowlist during remediation. Do not run or request formatters, fixers, tests, Clippy, Bazel commands, generators, or alternate Cargo commands as supporting evidence.

## Produce the successor patch

1. Build the intended changed-path set from the carried patch, dependency upgrade, Cargo-produced dependency files, contained remediations or pins, and explicit release-specific additions, then apply the recorded artifact exclusions. Account for new files explicitly; `git diff HEAD` does not include untracked files.
2. Generate the successor patch from `HEAD` with `git diff --binary --no-ext-diff HEAD -- <intended-paths...>`. Never include unrelated work and never overwrite the previous patch.
3. Run the helper's final audit against the pre-application baseline. Require unchanged predecessor bytes, `HEAD`, and index entries; preserved unrelated pre-existing edits; intended paths; and byte-for-byte equality with the intended Git export. The helper runs cached applicability when the index is pristine and reverse applicability against the patched worktree. If cached validation is unavailable, preserve the index and report that a separately authorized clean target is required.
4. Compare the previous and successor patches with `scripts/compare_patch_hunks.py` and classify every difference as one of:
   - byte-identical carried edit;
   - upstream-aware semantic rebase;
   - dependency upgrade or lockfile consequence;
   - contained build remediation;
   - dependency pin;
   - explicit release-specific addition.
5. After the audit passes, follow [the repository lifecycle](references/repository-lifecycle.md) to retain a byte-identical versioned copy in `upgrade-codex-patch/assets/patches/`, keeping the local successor as well. Then stage, commit, and push everything in the canonical `agentic-skills` repository, including pre-existing changes and deletions. Require verified upstream publication before reporting the upgrade as finished.
6. Report the target release and base commit; local and packaged successor paths, SHA-256, byte size, line count, path count, and hunk count; comparison classifications and separate applicability results; successful installation results for `codex`, `logs_client`, and `codex-code-mode-host`; retained or new pins; excluded command fallout; Codex index/worktree disposition; repository refresh result; and the `agentic-skills` commit hash, scope, push destination and result, and remaining unpublished commits. Use the helper's workspace-aware pin records instead of assuming which manifest owns a version.
7. State that only the four authorized Cargo commands were run during the upgrade/build phase. Do not ask permission for omitted repository commands or present their omission as incomplete verification.
8. Leave the Codex worktree unstaged and uncommitted unless the user separately authorizes those effects. The required final commit belongs to `agentic-skills`.

## Patch comparison helper

Use `scripts/compare_patch_hunks.py` for Git-style unified patches. It ignores index hashes, hunk offsets, and unchanged context; compares ordered added and removed lines; aligns identical hunk edit streams; reports new and removed file sections; and renders normalized diffs for changed edit streams. Its equality result proves identical added/removed lines, not byte-identical complete patch files. Use `--summary` only when exact differing lines are not needed.
