---
name: reconcile-completed-living-goal-status
description: "Reconcile stale mutable status in a user-designated living goal after authorized work reaches a terminal settled or applied state. Use when running, pending, blocked, awaiting-approval, or no-application prose remains operative after the underlying work changed."
---

# Reconcile Completed Living Goal Status

Update current status without rewriting protected decisions or overstating verification. Use the exact active goal path; do not switch to a historical attachment.

## Establish the terminal map

For each decision unit, record:

- its current state: `complete`, `applied`, `verified`, `superseded-gate`, `no-action`, or genuinely pending;
- the exact user-provenanced verdict;
- the authoritative evidence for the current state;
- every deliberately unrun check and why it is not a current requirement.

Do not infer completion from an agent recommendation, elapsed effort, or the absence of more findings.

## Reconcile proportionally

1. Replace operative `running`, `pending`, `blocked`, awaiting-approval, and no-application statements that conflict with the terminal map.
2. Keep former states only in a clearly attributable historical-status section.
3. Classify intentionally skipped but superseded gates as historical specifications, not unfinished work.
4. Prune duplicated snapshots after preserving a compact pointer to the verified and applied artifact.
5. State unrun build, test, formatting, generation, or publication work exactly; never imply it passed.
6. Run one narrow contradiction scan after the edit and do not version another audit while state is unchanged.

Edit only when the user authorized goal-document maintenance. Treat harness goal completion as a separate transition requiring direct user authority.

## Preserve both polarities

- Reconcile a plan whose remediation was applied while build verification remained prohibited.
- Leave a genuinely unresolved unit pending.
- Preserve an old blocked state as history without letting it appear as current status.
- Keep a broader historical product goal outside the active plan's completion claim.
