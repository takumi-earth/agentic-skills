---
name: separate-creation-and-enablement
description: "Model artifact creation, promotion, distribution, and activation as independent capability gates. Use when a workflow crosses several systems or authority domains and the agent must create useful artifacts now while proving that no later capability was exercised without explicit permission."
---

# Separate Creation and Enablement

Build an authority-and-effect matrix before acting. Treat every edge that grants another system the ability to discover, execute, distribute, or rely on an artifact as a separately gated capability.

## Build the capability matrix

For each proposed effect, record:

- the artifact and its current state;
- the mutator and destination;
- the capability newly granted by the effect;
- the user instruction authorizing that exact capability;
- whether the effect is reversible and how current state will be proven;
- positive evidence for the requested path and negative evidence for every ungranted edge.

Typical gates include `materialize`, `validate`, `adopt`, `promote`, `install`, `synchronize`, `link`, `register`, `enable`, `invoke`, and `publish`. Keep only gates that correspond to real effects in the current system, but never merge two merely because one command can perform both.

## Execute only granted edges

- A granted downstream edge does not retroactively authorize unrelated mutations; an activation request may still require a specific creation path.
- A granted creation edge does not authorize any downstream edge. Complete and validate the inert artifact, then stop at the last granted state.
- If the selected destination is already live through a symlink, watcher, import, or dynamic loader, classify the write as both mutation and activation before executing it.
- If one command bundles granted and ungranted edges, do not run it. Use a narrower official command when available or ask the user to authorize the bundled effect.

## Preserve the reviewable handoff

Return the capability matrix with actual state and evidence after execution. Identify the next ungranted edge without recommending it as inevitable. The user may choose to leave a useful artifact inert indefinitely.
