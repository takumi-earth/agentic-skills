---
name: preserve-application-readiness-across-git-representation-change
description: "Preserve or invalidate guarded remediation readiness from the application invariants that actually changed. Use when a safety commit, formatting, staging, or another Git representation change occurs after recovery evidence was prepared and the agent must not redo settled adjudication merely because HEAD or the index differs."
---

# Preserve Application Readiness Across Git Representation Change

Separate the settled verdict, application guards, and Git representation. Reassess only the axis whose authoritative input changed.

## Record the four readiness axes

1. `target-content`: exact guarded bytes or hashes for every effect path.
2. `restore-authority`: exact blob or source identity, availability, and bytes for every replacement.
3. `effect-shape`: selected paths and operations, including guarded deletions and no-op rules.
4. `index-preservation`: whether the application procedure can snapshot and restore the complete current index without altering its intended contents.

Record `HEAD`, staging state, and index identity separately as `representation`. A change in representation is informational unless the authorized application contract explicitly made that exact representation an invariant.

## Classify a later change

- If target content, restore authority, or effect shape changed, mark application blocked and name the mismatched invariant.
- If only `HEAD` or current index identity changed while a fresh complete-index preservation step remains valid, keep application ready.
- If index-preservation capability disappeared, block application even when source bytes match.
- Never convert a blocked application guard into renewed adjudication without direct user supersession of the settled verdict.

Do not reconstruct history, reset the index, or refresh evidence merely to make work appear current. Run only read checks already authorized by the active task.

## Validate counterfactuals

Cover a safety commit with unchanged targets, a staged formatting change with a preservable current index, one changed target byte, a missing restore object, a changed effect path, and loss of index-preservation capability.
