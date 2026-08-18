---
name: reconcile-completed-living-goal-status
description: "Generate a read-only reconciliation report for stale mutable statuses in a Markdown living goal. Use after substantive terminal state changes and before an authorized goal edit when blocked, pending, running, awaiting, or no-application prose may contradict a structured current-state ledger."
---

# Reconcile Completed Living Goal Status

Use the bundled report to identify contradictions. Keep editing and harness completion as separately authorized effects.

## Prepare current state

Provide JSON with user-provenanced terminal units:

```json
{"units":[{"id":"U1","current":"applied","evidence":"application-state.json state verified"}]}
```

Supported terminal values are `complete`, `applied`, `verified`, `superseded-gate`, and `no-action`. Mark retained chronology only between:

```markdown
<!-- goal-status-history:begin -->
...
<!-- goal-status-history:end -->
```

Run:

```bash
python3 scripts/report_status_reconciliation.py --state <state.json> --plan <goal.md>
```

The report tracks unit headings, finds high-signal operative stale status, and proposes one evidence-backed `STATUS` line per finding. It exits nonzero for contradictions and never writes the plan.

## Apply judgment outside the script

Confirm the exact active goal, read it through EOF, verify each ledger entry traces to user authority and current evidence, and preserve unrun verification boundaries. A clean report proves only consistency with the supplied state file; it does not establish correctness or authorize completion.

Validate a stale operative line, the same wording inside history markers, an unresolved unit, a missing evidence field, unmatched markers, and a clean terminal plan.
