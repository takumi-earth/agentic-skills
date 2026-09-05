---
name: upgrade-codex-patch
description: Rebase a versioned Codex Git patch onto a newer Codex release, resolve upstream hunk conflicts, run the Cargo upgrade/update/install sequence, contain small build remediations or pin the responsible dependency when fallout is wide-reaching, and produce an auditable successor patch. Use when carrying a patch such as `~/rust-forks/codex-v0.147.0.patch` to a newer release checkout or determining whether a formatter or fixer changed carried hunks. Do not use for general Rust dependency modernization without a carried Codex patch or for read-only patch inspection that does not execute the upgrade workflow.
---

# Upgrade Codex Patch

Carry the previous release patch forward without losing upstream behavior, then prove the provenance of every difference in the successor patch.

## Preserve the execution contract

- Resolve the Git top-level, target Codex release, previous patch path, successor patch path, and Cargo workspace directory before mutating anything.
- Read all applicable `AGENTS.md` files. Treat the user-requested sequence below as the authorized mutation surface; do not infer permission for checkout changes, fetches, formatting, fixing, tests, generators, staging, commits, pushes, or unrelated cleanup.
- If repository guidance requires an additional mutating command that the user did not authorize, surface the conflict before running it.
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

## Upgrade and build in order

Run these commands from `codex-rs` in exactly this order:

```bash
cargo upgrade --recursive --verbose
cargo update --recursive
cargo install --path cli
```

- Do not add `--incompatible`, `--pinned`, alternate feature flags, cache redirects, or substitute commands unless the user requests them.
- Let Rust commands wait for Cargo locks. Do not kill them merely because compilation is quiet or slow.
- If a command fails because of permissions, sandboxing, cache access, temporary-directory access, or network restrictions, rerun the same command through the harness escalation mechanism. Do not change the command's behavior to evade the restriction.
- After each mutating command, inspect the changed-path inventory and separate expected dependency or lockfile changes from unrelated pre-existing work.

## Remediate build failures

Trace each build failure to the dependency and API boundary that introduced it before choosing a remedy.

- Use contained code adaptation when the required change is small, cohesive, and owned by a limited number of files or call sites. Preserve upstream behavior and platform support.
- Pin the responsible dependency to a known working version when adapting it would require large, cross-crate, generated, protocol-wide, or otherwise wide-reaching changes.
- Establish a pin from concrete evidence such as the previous lockfile, previous manifest, or a version that built successfully. Do not guess a version or downgrade unrelated dependencies.
- Express a stability pin exactly when Cargo must not float to a newer compatible release, update resolution, and rerun the failed `cargo install --path cli` path.
- Repeat diagnosis and the smallest necessary remediation until installation succeeds or a material unresolved choice requires the user.
- Do not run `just fmt`, `just fix`, tests, Clippy, or repository generators unless separately authorized for this workflow.

## Prove optional formatter or fixer effects

When the user separately authorizes a formatter, fixer, or other extra source mutator:

1. Generate a patch snapshot immediately before the command.
2. Run the authorized command exactly as approved.
3. Generate another patch snapshot immediately afterward.
4. Compare the two artifacts:

```bash
python3 scripts/compare_patch_hunks.py <before.patch> <after.patch>
```

5. Attribute changes only from the normalized `+`/`-` streams and new or removed file sections. Formatting tools commonly produce no success output; silence proves nothing.

For a strict no-change gate, use:

```bash
python3 scripts/compare_patch_hunks.py --require-identical <before.patch> <after.patch>
```

Exit status `0` means the comparison completed and, with `--require-identical`, found no edit-stream or path-set differences. Exit status `1` means the strict comparison found differences. Exit status `2` means the inputs could not be parsed.

## Produce the successor patch

1. Build the intended changed-path set from the carried patch, dependency upgrade, contained remediations or pins, required generated files, and explicit release-specific additions.
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
6. State whether the successor patch was generated before or after every optional mutator. Do not claim that a command changed nothing without the corresponding artifact comparison.
7. Leave the worktree unstaged and uncommitted unless the user separately authorizes those effects.

## Patch comparison helper

Use `scripts/compare_patch_hunks.py` for Git-style unified patches. It ignores index hashes, hunk offsets, and unchanged context; compares ordered added and removed lines; aligns byte-identical hunks; reports new and removed file sections; and renders normalized diffs for changed edit streams. Use `--summary` only when exact differing lines are not needed.
