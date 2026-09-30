# Patch audit helper

`scripts/audit_upgrade.py` inspects the target repository with read-only Git commands. It neither applies nor exports a patch, runs Cargo, stages files, or edits repository content. Its optional `--output` exclusively publishes a JSON report outside the audited repository; an existing report is preserved. Use Python `3.11` or newer for `tomllib`.

Store task evidence under the canonical skill repository's `.scratchpad/upgrade-codex-patch/<run-id>/`. Use one pre-application baseline and one snapshot per meaningful phase or Cargo invocation, including remediation retries. These reports are workflow evidence, not additional build commands.

## Snapshot before applying the patch

Run from the verified target Git top-level. Substitute the resolved predecessor, artifact exclusions, run ID, and helper location; the paths below illustrate the current release lineage.

```bash
python3 ~/agentic-skills/upgrade-codex-patch/scripts/audit_upgrade.py snapshot \
  --repo . \
  --previous-patch ../codex-v0.159.0.patch \
  --exclude codex-rs/Cargo.lock \
  --output ~/agentic-skills/.scratchpad/upgrade-codex-patch/run-id/baseline.json
```

The snapshot records predecessor metadata, `HEAD` and exact release tag, semantic index identity, pre-existing tracked changes and untracked paths, and hashes of the expected mutation surface. It queries tracked and changed paths once, then reads carried paths, explicit inclusions/exclusions, changed files, and Cargo manifests/lockfiles. It reports read counts and resolves exact dependency pins through workspace inheritance, including target-specific dependencies.

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

Generate the patch through the skill's explicit path allowlist, applying the recorded exclusions. Then audit it against the original pre-application baseline:

```bash
python3 ~/agentic-skills/upgrade-codex-patch/scripts/audit_upgrade.py audit \
  --baseline ~/agentic-skills/.scratchpad/upgrade-codex-patch/run-id/baseline.json \
  --successor-patch ../codex-v0.159.2.patch \
  --output ~/agentic-skills/.scratchpad/upgrade-codex-patch/run-id/final-audit.json
```

Supply repeatable `--include` options for later explicitly authorized additions. The audit checks predecessor/`HEAD`/index preservation, intended paths and excluded fallout, preservation of unrelated tracked edits, exact Git-export bytes, cached applicability when the index is pristine, and reverse applicability against the patched worktree. It summarizes normalized edit-stream comparisons and current exact pins; inspect differing edits with `scripts/compare_patch_hunks.py` and classify them separately.

Pre-existing edits in exported paths and unaccounted new untracked files are reported as unresolved boundaries; explicitly excluded untracked command fallout remains outside the artifact. A path allowlist cannot distinguish unrelated hunks in the same file, and `git diff HEAD` omits untracked files. Preserve those files and resolve the export provenance through authorized patch mechanics; the helper never stages, cleans, or constructs another checkout. A non-pristine index produces a separate cached-applicability `not-run` result rather than a claim that it passed.

Exit status `0` means the inspection completed and applicable checks passed; `1` means preservation or audit checks failed; `2` means inputs, Git inspection, or report publication failed. JSON stdout remains machine-readable, and failures retain their checked condition plus expected and received values. An audit does not prove installation success: retain the exact Cargo exit statuses and installation output for all three executables separately.
