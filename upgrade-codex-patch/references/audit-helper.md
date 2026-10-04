# Patch audit helper

`scripts/audit_upgrade.py` inspects the target repository with read-only Git commands. It neither applies nor exports a patch, runs Cargo, stages files, or edits repository content. Its optional `--output` exclusively publishes a JSON report outside the audited repository; an existing report is preserved. Applicability uses an automatically cleaned filesystem view under the explicit external `--scratch-root`, without constructing or modifying any Git index. Use Python `3.11` or newer for `tomllib`.

Store task evidence under the canonical skill repository's `.scratchpad/upgrade-codex-patch/<run-id>/`. Use one pre-application baseline and one snapshot per meaningful phase or Cargo invocation, including remediation retries. These reports are workflow evidence, not additional build commands.

## Snapshot before applying the patch

Run from the verified target Git top-level. Substitute the resolved predecessor, artifact exclusions, run ID, and helper location; the paths below illustrate the current release lineage.

```bash
python3 ~/agentic-skills/upgrade-codex-patch/scripts/audit_upgrade.py snapshot \
  --repo . \
  --previous-patch ~/agentic-skills/upgrade-codex-patch/assets/patches/codex-v0.160.0.patch \
  --exclude codex-rs/Cargo.lock \
  --output ~/agentic-skills/.scratchpad/upgrade-codex-patch/run-id/baseline.json
```

The snapshot records predecessor metadata, `HEAD` and exact release tag, semantic index identity and index bytes, pre-existing tracked changes and untracked paths, and hashes of the expected mutation surface. It queries tracked and changed paths once, then reads carried paths, explicit inclusions/exclusions, changed files, and Cargo manifests/lockfiles. It reports read counts and resolves exact dependency pins through workspace inheritance, including target-specific dependencies. Optional Git locks and filesystem-monitor queries are disabled for inspection.

When the predecessor is already applied, the snapshot hashes both the worktree and staged exports of its paths. An exact predecessor match establishes that existing selection. An index match does not approve additional unstaged hunks in the same files. Freeze the reviewed selection separately; source paths alone cannot distinguish intended edits from automatic version changes or user work. Older snapshots without these digests keep their conservative boundary.

Add repeatable `--include <repo-relative-file>` options for explicitly authorized additions. These options record intended paths; they grant no edit authority. The same snapshot scope must be used when comparing consecutive snapshots. Preserve output paths beneath home as `~/...` in evidence.

## Account for each command

Take a snapshot after patch application as the first Cargo comparison input, then another after each Cargo invocation. Use the same predecessor and exclusions. Compare the immediately preceding state with the new snapshot:

```bash
python3 ~/agentic-skills/upgrade-codex-patch/scripts/audit_upgrade.py changes \
  --before ~/agentic-skills/.scratchpad/upgrade-codex-patch/run-id/applied.json \
  --after ~/agentic-skills/.scratchpad/upgrade-codex-patch/run-id/upgraded.json
```

The JSON separates dependency files from other changed paths and reports newly untracked files plus preservation of `HEAD`, index entries, and predecessor metadata. Classify the actual changes using the governing patch intent; a filename alone does not prove that a change is expected. Introduce a newly authorized inclusion before both snapshots of the affected command rather than changing scope between them.

## Audit the final successor

Prepare the reviewed field/hunk selection under [the selection contract](patch-selection.md), applying the recorded exclusions. Freeze it as a separate input before generating the successor; do not copy an unreviewed candidate merely to satisfy the equality check. The audit has no whole-worktree export fallback. Then audit against the original baseline:

```bash
python3 ~/agentic-skills/upgrade-codex-patch/scripts/audit_upgrade.py audit \
  --baseline ~/agentic-skills/.scratchpad/upgrade-codex-patch/run-id/baseline.json \
  --successor-patch ../codex-v0.161.0.patch \
  --selected-export ~/agentic-skills/.scratchpad/upgrade-codex-patch/run-id/reviewed-export.patch \
  --scratch-root ~/agentic-skills/.scratchpad/upgrade-codex-patch/run-id \
  --output ~/agentic-skills/.scratchpad/upgrade-codex-patch/run-id/final-audit.json
```

Supply repeatable `--include` options for later authorized additions, including untracked source. The audit checks predecessor/`HEAD`/index preservation, intended paths and excluded fallout, preservation of unrelated tracked edits, exact equality with the frozen reviewed export, cached applicability when the index is pristine, and target-base applicability in a private filesystem view of `HEAD`. It summarizes normalized edit-stream comparisons and current exact pins; inspect differing edits with `scripts/compare_patch_hunks.py` and classify them separately.

Pre-existing edits in exported paths without recorded predecessor provenance, and unaccounted untracked files, remain unresolved boundaries. Authorized untracked additions must appear in the selected artifact; they do not need staging. The helper never stages, cleans or creates another Git index. A non-pristine index skips only the additional cached check; target-base applicability still runs independently. Ordinary versions refreshed in the live checkout are not required to match patch context, so reverse application against that checkout is not an audit gate.

Exit status `0` means the inspection completed and applicable checks passed; `1` means preservation or audit checks failed; `2` means inputs, Git inspection, or report publication failed. JSON stdout remains machine-readable, and failures retain their checked condition plus expected and received values. An audit does not prove installation success: retain the exact Cargo exit statuses and installation output for all three executables separately.
