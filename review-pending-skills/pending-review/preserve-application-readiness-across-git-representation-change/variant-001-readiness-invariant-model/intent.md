# Readiness invariant-model variant

## Concrete intent

Keep guarded remediation application ready when a safety commit, formatting, or staging changes only Git representation and leaves application inputs valid.

## Approach

Model four independent axes: guarded target content, restore-object authority, effect-path identity, and index-preservation capability. Record HEAD and current index identity as representation facts rather than automatic verdict or readiness gates.

## Preserved nuance

A target-byte or restore-object change blocks application, but does not by itself reopen a user-settled verdict. An index may change before application if the authorized procedure snapshots and restores the then-current complete index.

## Relationships and uncertainty

This overlaps `$filesystem-git-observability` and `$audit-rollout-damage`. Review should decide whether the invariant matrix belongs in those owners instead of a standalone skill.

## Review questions

- Which recovery methods require an exact preexisting index identity rather than a fresh application-time snapshot?
- How should unreachable but byte-copied restore objects be represented?
