# Guarded application readiness

Use this reference when an authorized filesystem or Git application already has prepared guard evidence and a later change may affect its readiness. Compare only inputs and checks authorized by that application contract; this reference does not require a new snapshot, report, history reconstruction, or audit.

## Keep the application invariants explicit

Assess four independent axes using the authorized method's actual requirements:

| Axis | Required evidence |
| --- | --- |
| `target-content` | The exact guarded bytes, hashes, or allowed absence for every selected effect path. |
| `restore-authority` | The approved source identity, current availability, and required bytes for every replacement. Require replacement sources only for operations that need them. |
| `effect-shape` | The selected paths and operations, including guarded deletion and already-satisfied-state rules. Matching path names alone does not establish the same operation. |
| `index-preservation` | The authorized method's ability to preserve the complete index state required by the application contract. A capability label alone does not establish that the method remains usable. |

Two matching snapshots do not establish readiness when their records are malformed, incomplete, or describe unavailable replacement sources. Identify missing guard coverage or unavailable evidence before relying on the comparison.

## Classify changes by the contract they affect

- Record `HEAD`, staging state, and index identity as representation facts unless the authorized method explicitly depends on their exact values. A method that pins `HEAD` or the preexisting index must retain those guards.
- Keep application ready after a representation change only when every required application invariant remains satisfied and the required index-preservation method remains available.
- Treat formatting that changes guarded target bytes as content drift. A formatting or staging label cannot establish that only representation changed.
- When the authorized procedure preserves a fresh complete index, preserve the index present at application time. Do not restore an older index merely to reproduce an earlier evidence snapshot.
- Stop the dependent application when a required invariant fails or cannot be established. Name the affected condition and its expected and received state; preserve unrelated valid evidence.

Keep the user's selected disposition settled while application readiness changes. `$maintain-living-goal` owns the separate decision, application, and verification states. A failed guard does not reopen adjudication or authorize a blanket re-audit.

## Check both readiness and invalidation

Cover a safety commit with unchanged guarded inputs; a changed current index that the authorized method can preserve; an explicitly pinned `HEAD` or index that changes; formatting that changes a guarded target; a missing replacement source; a changed effect operation; a deletion requiring no replacement source; and loss of index-preservation capability.
