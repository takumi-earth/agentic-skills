---
name: reconcile-completed-living-goal-status
description: "Generate a read-only reconciliation report for stale mutable statuses in a Markdown living goal. Use after substantive terminal state changes and before an authorized goal edit when blocked, pending, running, awaiting, or no-application prose may contradict a structured current-state ledger."
---

# Reconcile Completed Living Goal Status

Use the bundled report to identify contradictions. Keep editing and harness completion as separately authorized effects.

## Prepare current state

Use an existing JSON state record with attributable evidence for each selected unit; classification does not authorize creating a ledger:

```json
{"units":[{"id":"U1","current":"applied","dimension":"application","evidence":"application-state.json: application observed for the current inputs"}]}
```

Supported terminal values are `complete`, `applied`, `verified`, `superseded-gate`, and `no-action`. `dimension` may be `decision`, `application`, or `verification`. Legacy `applied`/`no-action` records concern application, `verified` concerns verification, and `superseded-gate` concerns decision state. An unqualified `complete` record cannot establish a dimension or harness completion. Mark retained chronology between:

```markdown
<!-- goal-status-history:begin -->
...
<!-- goal-status-history:end -->
```

Run:

```bash
python3 scripts/report_status_reconciliation.py --state <state.json> --plan <goal.md>
```

The report tracks unit headings through subsections and excludes history and fenced examples. For a same-dimension status such as `application: PENDING; verification: NOT RUN (prohibited)`, it may propose replacing only `PENDING` with `APPLIED`; it preserves every other part of the line. Application evidence never changes verification status. Explicit unrun or prohibited verification remains protected even when earlier evidence says `verified`.

Ambiguous legacy prose produces `needs-context` with `proposed_line: null`, not a whole-line replacement. Definite supported field conflicts use `dimension-status-conflict`. Exit `1` means findings require review, exit `0` means no finding within the supported format, and malformed inputs exit `2`. No code path writes the plan or changes harness status.

## Apply judgment outside the script

Confirm the exact active goal, read it through EOF, and verify each supplied observation's authority, input identity, and current applicability. Separate the selected decision, its application, its verification, and the user's completion decision. A clean report covers only the supported textual checks against supplied observations; it does not establish correctness or authorize completion.

Validate a stale operative line, the same wording inside history markers, an unresolved unit, a missing evidence field, unmatched markers, and a clean terminal plan.
