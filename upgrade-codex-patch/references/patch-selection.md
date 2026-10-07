# Select the changes that belong in a Codex patch

The patch carries deliberate behavior and compatibility decisions. Cargo's
routine version refresh is command fallout, and the lockfile is always excluded.

## Select the authoritative input

Use the exact patch the user selects. Record its bytes and digest before editing
or applying it. A stale local artifact with the same release name does not
override a selected packaged patch and does not require another decision.

For a requested revision of the current release's patch, preserve its original
bytes in task evidence, prepare a separate candidate, audit that candidate, then
replace only the selected artifact with a guard against intervening edits. Do
not treat an older local copy as the export source or overwrite it implicitly.

## Classify changes at the field or hunk level

| Change | Selection |
| --- | --- |
| Workspace resolver | Retain the resolver change |
| Dependency pin introduced, changed or removed | Retain the complete intentional constraint change and its reason |
| Dependency added or removed | Retain the dependency declaration, including its version when required |
| Features, default features, workspace inheritance, source/revision, target tables, build configuration | Retain the necessary non-version manifest changes |
| Source fixes and integration changes | Retain the reviewed implementation and required tests or generated surfaces |
| Ordinary version bump of an existing dependency | Exclude; the required `cargo upgrade` and `cargo update` rounds cover it |
| `Cargo.lock` resolution changes | Exclude; `cargo update` refreshes it |

An explicitly approved baseline remains the baseline. New automatic version
changes do not inherit approval because they share a file, line or diff hunk with
an intentional change.

The upgrade workflow always runs `cargo upgrade` and `cargo update`. Source/API
migrations do not create an exception for ordinary version bumps of existing
dependencies, including raising a compatible minimum version. Retain dependency
version changes for genuine additions, removals, or introduced/changed/removed
pins; retain required non-version manifest changes separately.

Read staged and unstaged diffs when the user identifies that split as their
selection evidence. Preserve the exact index and staging split. Otherwise do
not assume unrelated staged work belongs to the patch. Never stage, unstage,
reset, restore or use a temporary Git index to manufacture an export.

For example, a staged resolver/pin/feature change and an unstaged ordinary bump
in the same `Cargo.toml` are separate units. Preserve the selected constraint or
feature while keeping the refreshed ordinary version in the live worktree.

## Keep selection independent of Cargo fallout

Before Cargo, prepare the rebased, reviewed patch selection from the target
release base. Preserve that selection while Cargo refreshes manifests and the
lockfile. After a compatibility repair, add only its approved source changes,
pin changes and non-version manifest fields to the selection.

Use an explicitly reviewed existing index only when the user designates it as
the selection. Read its diff without modifying it. For mixed hunks or later
unstaged repairs, maintain a private curated filesystem view or edit the
candidate's reviewed hunks against the verified release base. This view is an
artifact preparation input; builds still use the live checkout. It must not
reset live manifest versions or create another Git index.

Whole-file `git diff HEAD -- <paths>` is diagnostic input, not an export rule.
It admits automatic version noise and unrelated hunks in selected files, and
omits new untracked source. Account for authorized new files explicitly.

Freeze the final reviewed export in task evidence before publishing the
candidate. Supply it to the audit as `--selected-export`; the candidate must
match these bytes. The audit verifies applicability against a private filesystem
materialization of the real target `HEAD`, independent of the user's staged
index and of ordinary versions updated in the live checkout. Do not require
reverse application against that checkout or relax selection to make it pass.

## Diagnose warnings before choosing a source fix

Installation success does not close warnings. Inspect unique sites, their
owners, feature/platform conditions and the intended behavior. An unused import
can indicate a lost call site, a debug-only use or a redundant local type name
whose values still flow through another type. Trace that distinction before
deleting anything. Apply only authorized remediation and report remaining
warnings separately; do not invoke blanket fixers or suppress diagnostics.
