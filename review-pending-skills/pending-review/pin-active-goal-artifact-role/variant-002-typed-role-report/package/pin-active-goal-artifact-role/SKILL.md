---
name: pin-active-goal-artifact-role
description: "Produce a typed, read-only attribution report for one exact active goal and its explicitly referenced historical or evidence artifacts. Use before plan-status or completion reporting when path roles are easy to confuse and a deterministic role check is warranted."
---

# Pin Active Goal Artifact Role

Use the bundled report to prove artifact roles before reasoning about status. Do not use it to discover sibling attachments or to grant any task effect.

## Build the report

Run:

```bash
python3 scripts/render_goal_roles.py --active <exact-goal-path> --reference historical=<path> --reference evidence=<path>
```

Pass only paths already designated by the harness, the user, or the active goal. The script reads the active file, requires every secondary path to appear in it, rejects duplicate or conflicting roles, and emits normalized JSON to stdout.

## Interpret the report narrowly

- Source mutable goal status only from the `active` entry and current authoritative state.
- Use `historical` entries only for attributable chronology.
- Use `evidence` entries only for the facts their evidence contract supports.
- Treat an omitted path as unclassified, not as safe to inspect.
- Stop if competing active paths exist; this report accepts exactly one.

The report is read-only. It does not authorize an edit, task execution, attachment enumeration, or a goal-status transition.

## Validate before relying on it

Exercise an accepted literal reference, a missing reference, a conflicting duplicate, a nonexistent active file, and a home-relative path. Confirm stderr carries failures and stdout remains machine-readable JSON on success.
