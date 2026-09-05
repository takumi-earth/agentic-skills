# Authority topology contract

## Required authorities

Keep these roots independent:

| Authority | Source | Permitted use | Forbidden inference |
| --- | --- | --- | --- |
| Package resources | Invoked package location | Read resources shipped with the package | Harness state or canonical repository identity |
| Harness state | Explicit argument or inherited environment | Read harness-owned configuration and state | Resolved `__file__` parents |
| Canonical repository | Explicit caller selection | Read canonical repository-owned state | Copied or linked package parent |
| Task output | Validator-owned disposable root | Write declared fixture output | Package, harness, repository, or external paths |

## Fixture topology

Execute the target package directly, as a complete copy, through a relative directory symlink, and through an absolute directory symlink. When the target declares sibling-package dependencies, reproduce every dependency as a copy or the corresponding relative or absolute symlink in the same lexical fixture repository.

Use identical target arguments and explicit authorities across all four rows. Compare authorities as resolved paths, accepting absolute and `~/...` spellings. Normalize whole package and task-output path values and their descendants before comparing target JSON; preserve paths embedded in ordinary text and distinct paths that merely share a prefix. Never normalize an authority mismatch into parity.

Create fixture repositories beneath the selected canonical repository's `.scratchpad/`, or an explicit existing `--scratch-root` outside the selected packages. Preserve existing scratch content. Exclude only the owned temporary directory from intermediate protected-tree observations, remove that directory, then compare the complete protected trees. Remove a scratch parent only when the validator created it and it is still empty.

## Negative evidence

- Omit runtime authority and require failure without parent walking.
- Omit a declared sibling from copied and linked fixture repositories and require failure.
- Execute a target that derives runtime state from `Path(__file__).resolve().parents[...]` and require parity failure.
- Check declarations against observed output files, directories, and symlinks. Compare actual artifact bytes and metadata, including empty directories; permit an empty declaration for read-only targets.
- Reject observed fixture mutations outside the current task-output directory. Preserve nested result fields named `topology`; only the reserved top-level field is metadata.
- Observe canonical repository and runtime state before and after execution, including directory existence and permissions. Stop later rows after an observed protected-state or fixture mutation, and retain their unexecuted status.

## Observation limits

The validator observes the supplied repository and runtime roots, its controlled fixture, and declared output artifacts. It does not sandbox target processes, scan the host for undeclared external writes, or detect changes reverted between observations. These limits appear in the JSON report. A passing matrix proves the stated observed parity, not unrestricted filesystem containment.
