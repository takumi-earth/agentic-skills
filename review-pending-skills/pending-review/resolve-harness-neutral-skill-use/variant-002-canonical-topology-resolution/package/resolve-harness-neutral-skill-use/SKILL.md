---
name: resolve-harness-neutral-skill-use
description: "Resolve exact caller-supplied skill projections into lexical path, canonical target, symlink, and content-identity facts. Use when trace analysis spans canonical, copied, or symlinked harness skill roots and needs topology evidence without installing, syncing, or scanning unrelated directories."
---

# Resolve Harness-Neutral Skill Use

Resolve topology before interpreting transcript path evidence. Inspect only explicit projections.

## Report exact projections

Run:

```bash
python3 scripts/resolve_skill_topology.py --projection codex=~/.agents/skills/example-skill --projection canonical=~/agentic-skills/example-skill
```

Each projection may name a package directory or its `SKILL.md`. The report includes:

- the lexical path as supplied;
- whether that path or package is a symlink;
- the resolved canonical `SKILL.md` path;
- SHA-256 and filesystem identity for the body;
- content groups for byte-identical projections.

Do not collapse distinct copied packages into one mutable identity solely because their current bytes match. Use canonical target equality for symlink identity and retain content groups as a separate observation.

## Keep deployment inert

Do not enumerate harness roots, create links, synchronize packages, or modify a projection. Correlate this topology report with transcript references in a separate read-only step.

Validate direct canonical paths, relative and absolute symlinks, byte-identical copies, divergent copies, missing `SKILL.md`, duplicate labels, and a path outside the home directory. Normalize home paths only in rendered output.
