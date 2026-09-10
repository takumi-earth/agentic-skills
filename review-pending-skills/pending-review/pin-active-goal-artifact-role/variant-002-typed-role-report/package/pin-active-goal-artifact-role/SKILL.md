---
name: pin-active-goal-artifact-role
description: "Produce a typed, read-only attribution report for one exact active goal and its explicitly referenced historical or evidence artifacts. Use before plan-status or completion reporting when path roles are easy to confuse and a deterministic role check is warranted."
---

# Pin Active Goal Artifact Role

Use the bundled report to distinguish caller-declared roles from verified path mentions before reasoning about status. A matching path does not prove its semantic role, authority, existence, or evidence contents. Do not use it to discover sibling attachments or to grant any task effect.

## Build the report

Run:

```bash
python3 scripts/render_goal_roles.py --active <exact-goal-path> --reference historical=<path> --reference evidence=<path>
```

Pass only paths already designated by the harness, the user, or the active goal. CLI-relative paths resolve from the current working directory. The script reads the active file once, requires each secondary path to have a complete delimited spelling in it, rejects duplicate or conflicting roles, and emits normalized JSON to stdout.

Supported spellings are absolute, `~/...`, or relative to the active goal's directory, including `./...`, in whitespace, code, quotes, or ordinary Markdown link delimiters. Prefix matches such as `goal.md.backup` do not match `goal.md`. Encoded URLs, link-reference indirection, and paths with appended fragments are outside this literal interface. Match lines use LF addressing; the active hash covers the original bytes.

`role_source: caller-declared` applies to every entry. `text_reference_verified` confirms only a matching path mention at `reference_lines`; `artifact_contents_verified: false` makes the secondary-read limit explicit. `status_authority` repeats the supplied designation rather than independently establishing it.

## Interpret the report narrowly

- Source mutable goal status only from the `active` entry and current authoritative state.
- Use `historical` entries only for attributable chronology.
- Use `evidence` entries only for the facts their evidence contract supports.
- Treat an omitted path as unclassified, not as safe to inspect.
- Stop if competing active paths exist; this report accepts exactly one.

The report is read-only. It does not authorize an edit, task execution, attachment enumeration, or a goal-status transition.

## Validate before relying on it

Exercise an accepted literal reference, a missing reference, a conflicting duplicate, a nonexistent active file, and a home-relative path. Confirm stderr carries failures and stdout remains machine-readable JSON on success.
