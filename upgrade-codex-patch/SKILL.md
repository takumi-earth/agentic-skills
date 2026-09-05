---
name: upgrade-codex-patch
description: Rebase a versioned Codex Git patch onto a newer Codex release, resolve upstream hunk conflicts, run only the exact Cargo upgrade/update/install sequence, contain small build remediations or pin the responsible dependency when fallout is wide-reaching, and produce an auditable successor patch. Use when carrying a patch such as `~/rust-forks/codex-v0.147.0.patch` to a newer release checkout. Do not use for general Rust dependency modernization without a carried Codex patch or for read-only patch inspection that does not execute the upgrade workflow.
---

# Upgrade Codex Patch

Carry the previous release patch forward without losing upstream behavior, then prove the provenance of every difference in the successor patch.

## Preserve the execution contract

- Resolve the Git top-level, target Codex release, previous patch path, successor patch path, and Cargo workspace directory before mutating anything.
- Read all applicable `AGENTS.md` files. This workflow's explicit command contract supersedes repository guidance that would otherwise require formatting, fixing, tests, Clippy, generators, or other repository commands outside the patch mechanics and three-command Cargo sequence below.
- Do not run or ask to run `just fmt`, `just fix`, tests, Clippy, `just bazel-lock-update`, other generators, or substitute repository commands. Do not treat their omission as a blocker. A future explicit user instruction may change the contract, but the skill must never solicit that expansion.
- Apart from patch inspection, application, source remediation, comparison, and successor-artifact operations required by this workflow, the only commands permitted are the three Cargo commands listed below. Do not infer permission for checkout changes, fetches, staging, commits, pushes, or unrelated cleanup.
- Keep the previous patch immutable. Record its SHA-256 digest, byte size, line count, and changed-path inventory.
- Inspect the worktree and index before applying the patch. Preserve unrelated user changes and exclude them from the successor patch.
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

Run these commands from `codex-rs` in exactly this order:

```bash
cargo upgrade --recursive --verbose
cargo update --recursive
cargo install --path cli
```

- Treat these commands as a complete build-command allowlist, not the start of a broader repository workflow. Repository guidance cannot add a formatter, fixer, test, lint, generator, lockfile-maintenance, or substitute command.
- Do not add `--incompatible`, `--pinned`, alternate feature flags, cache redirects, or substitute commands unless the user requests them.
- Let Rust commands wait for Cargo locks. Do not kill them merely because compilation is quiet or slow.
- If a command fails because of permissions, sandboxing, cache access, temporary-directory access, or network restrictions, rerun the same command through the harness escalation mechanism. Do not change the command's behavior to evade the restriction.
- After each Cargo command, account for the resulting changed paths through the patch-inspection workflow and separate expected dependency or lockfile changes from unrelated pre-existing work. Do not invoke an extra repository mutator to reconcile them.

## Remediate build failures

Trace each build failure to the dependency and API boundary that introduced it before choosing a remedy.

- Use contained code adaptation when the required change is small, cohesive, and owned by a limited number of files or call sites. Preserve upstream behavior and platform support.
- Pin the responsible dependency to a known working version when adapting it would require large, cross-crate, generated, protocol-wide, or otherwise wide-reaching changes.
- Establish a pin from concrete evidence such as the previous lockfile, previous manifest, or a version that built successfully. Do not guess a version or downgrade unrelated dependencies.
- Express a stability pin exactly when Cargo must not float to a newer compatible release, update resolution, and rerun the failed `cargo install --path cli` path.
- Repeat diagnosis and the smallest necessary remediation until installation succeeds or a material unresolved choice requires the user.
- Keep the same command allowlist during remediation. Do not run or request formatters, fixers, tests, Clippy, Bazel commands, generators, or alternate Cargo commands as supporting evidence.

## Produce the successor patch

1. Build the intended changed-path set from the carried patch, dependency upgrade, Cargo-produced dependency files, contained remediations or pins, and explicit release-specific additions.
2. Generate the successor patch from `HEAD` with `git diff --binary --no-ext-diff HEAD -- <intended-paths...>`. Never include unrelated work and never overwrite the previous patch.
3. If the index still represents the pristine target release, validate applicability without changing it using `git apply --check --cached <successor-patch>`. If the index is not pristine, preserve it and report that a separate clean target is required for applicability validation.
4. Compare the previous and successor patches with `scripts/compare_patch_hunks.py` and classify every difference as one of:
   - byte-identical carried edit;
   - upstream-aware semantic rebase;
   - dependency upgrade or lockfile consequence;
   - contained build remediation;
   - dependency pin;
   - explicit release-specific addition.
5. Report the successor patch path, SHA-256 digest, size, line count, applicability result, successful install command, any pins, and the hunk-comparison summary.
6. State that only the three authorized Cargo commands were run during the upgrade/build phase. Do not ask permission for omitted repository commands or present their omission as incomplete verification.
7. Leave the worktree unstaged and uncommitted unless the user separately authorizes those effects.

## Patch comparison helper

Use `scripts/compare_patch_hunks.py` for Git-style unified patches. It ignores index hashes, hunk offsets, and unchanged context; compares ordered added and removed lines; aligns byte-identical hunks; reports new and removed file sections; and renders normalized diffs for changed edit streams. Use `--summary` only when exact differing lines are not needed.
