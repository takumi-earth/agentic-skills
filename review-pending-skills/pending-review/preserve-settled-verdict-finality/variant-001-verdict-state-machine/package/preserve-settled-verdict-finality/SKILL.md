---
name: preserve-settled-verdict-finality
description: "Preserve the finality of user-settled or applied decision units in plans, recovery ledgers, and remediation workflows. Use when later context, Git representation changes, stale prose, or new guard facts could tempt an agent to recreate reassessment or countersignature work."
---

# Preserve Settled Verdict Finality

Treat decision finality and application readiness as separate axes. A failed or stale application guard can block an effect without reopening the decision that selected it.

## Use explicit states

Model each decision unit as one of:

- `unresolved`: the user has not selected an outcome;
- `proposed`: an agent recommendation awaits the user;
- `settled`: the user selected the outcome;
- `applied`: the settled outcome was applied;
- `superseded-gate`: an older verification gate is no longer required by the authorized path;
- `superseded-by-user`: the user directly replaced the prior outcome.

Only an attributable user instruction may move `settled` or `applied` back into decision work. Agent findings, a commit, a changed index, a compaction summary, or stale plan wording cannot do so.

## Guard the next action

1. Identify the exact unit and its user-provenanced verdict.
2. Classify new information as verdict evidence, application-guard evidence, or representation-only change.
3. Preserve the verdict unless the user explicitly supersedes it.
4. If an application guard fails, report the guard mismatch and stop that effect; do not manufacture new approval boxes.
5. Keep former statuses only as attributable history.

Never convert `settled` into `proposed` merely to obtain reassurance. Never claim user supersession from an assistant-authored plan or recommendation.

## Test counterexamples

- Preserve finality across a safety commit that leaves guarded bytes and restore objects intact.
- Block application on changed target bytes without reopening the verdict.
- Permit reopening only when the user names or unambiguously identifies the unit and replaces its prior outcome.
