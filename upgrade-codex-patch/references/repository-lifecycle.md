# Canonical repository and patch resources

Every upgrade starts by refreshing the canonical `agentic-skills` checkout and ends by retaining the audited patch, committing all changes in that repository, and pushing them to its canonical upstream. `$manage-agentic-skills-repo` owns the shared pull, complete repository commit, and push workflow; this reference owns patch retention and the upgrade's publication evidence. Keep these Git effects separate from the protected Codex checkout. A current user instruction may narrow or override them.

## Refresh before choosing or applying a patch

Use `$manage-agentic-skills-repo` before choosing a predecessor, changing the Codex checkout, applying a patch, or running Cargo. Resolve the activated package through directory symlinks; for an installed copy, use the selected canonical checkout, `AGENTIC_SKILLS_REPO`, or `~/agentic-skills`. If the synchronized shared skill is unavailable, read `manage-agentic-skills-repo/SKILL.md` in that canonical checkout directly. Before the shared pull, verify that the configured upstream's fetch remote identity is `github.com/takumi-earth/agentic-skills`. Do not treat a matching directory name, push URL, or unrelated Git parent as proof. If the checkout or canonical upstream cannot be resolved, stop before changing Codex.

Follow the shared skill's pull, integration, and publication workflow without another permission request. A successful refresh already performed for this invocation satisfies refresh; do not repeat it merely because this reference was loaded. Use the refreshed canonical package for the rest of the invocation, and read refreshed `AGENTS.md`, `upgrade-codex-patch/SKILL.md`, and required resources completely before proceeding.

Use an explicitly named predecessor when supplied; that selection settles differing copies. Do not substitute a local artifact with the same release name or demand that it match. Otherwise inspect the applicable `codex-v*.patch` resources in `upgrade-codex-patch/assets/patches/` alongside local versioned artifacts; compare release versions rather than lexical filenames and resolve genuinely ambiguous provenance. Preserve predecessor bytes and older packaged patches.

## Retain the audited successor

Keep the external successor at its selected local destination and retain an additional versioned copy at `upgrade-codex-patch/assets/patches/codex-v<target-release>.patch`. Copy only after the final audit, authorized Cargo sequence, and complete package preparation succeed. The user's final runtime handoff is separately reserved; finish retention and publication before presenting that command, without waiting for or initiating live replacement. Use the audit's SHA-256 so a source change between audit and retention is rejected:

```bash
python3 "<skills-repo>/upgrade-codex-patch/scripts/retain_patch.py" \
  "<local-successor-patch>" --sha256 "<audited-sha256>"
```

The helper resolves its package through symlinks and atomically publishes the bytes without replacing an existing resource. An identical existing file is an unchanged result; different bytes, a destination symlink, or an escaping resource directory stop retention without overwriting existing work. Successful JSON gives the source, resource, digest, byte size, outcome, and resource write count; failures report the checked condition, expected value, and received value. Exit `0` means retained or already identical; exit `2` means retention failed. The helper does not perform the patch audit or any Git operation.

For an explicitly requested same-release revision, follow the selection contract:
preserve the selected artifact's original bytes in evidence, audit a separate
candidate, then guard replacement of only the selected destination against its
recorded original digest. The normal retention helper's conflicting-file refusal
does not authorize deleting the resource or publishing an alternate patch variant.

Keep `assets/patches/.gitattributes` with the resources. It disables Git text conversion for `*.patch`, preserving the audited bytes on machines with different `core.autocrlf` settings. It also preserves the required space on blank unified-diff context lines without treating that literal patch syntax as a whitespace error.

Use `--skill-root "<canonical-package>"` only when explicitly selecting the already-resolved canonical package. Installed copies are not retention destinations. Keep supporting audit snapshots and command logs under `.scratchpad/`; the versioned patch itself is a deployable package resource.

## Commit and push everything at the conclusion

After retaining the exact audited bytes, follow `$manage-agentic-skills-repo` to run `git add .` from the canonical Git top-level, review every staged diff, and commit the complete repository scope, including pre-existing and unfamiliar edits, new files, and deletions. Before its commit step, verify that the retained patch is tracked in the index and matches the audited digest. The shared skill owns complete-diff message coverage, the repository's commit convention, normal hooks, and failure handling. Keep ignored scratch evidence ignored.

If nothing is staged because the complete desired state is already committed, use the existing commit instead of creating an empty commit, then continue with publication. Otherwise confirm the new commit and inspect remaining status; report any hook fallout or concurrent changes rather than claiming a clean repository.

Verify every configured push URL for the upstream remote has the canonical repository identity, then follow the shared skill's push and publication checks. Require a successful push and fresh confirmation that the upstream contains the pushed commit; report incoming and outgoing counts separately. Reconcile incoming commits through the shared workflow when a push is rejected; never force-push, rewrite local history, or bypass hooks. A failed resource copy, commit, push, or publication check leaves the upgrade's repository conclusion unfinished.

Report the refresh result, both successor destinations and their shared digest, the commit hash and staged scope, push destination and exit status, verified upstream publication, remaining worktree/index changes, and outgoing commits. The committed skill and patch must be available from the upstream before reporting completion.
