---
name: separate-review-evidence-effects
description: "Audit a skill package for wording that implicitly turns review authority into artifact creation, helper execution, verification, mutation, Git, or activation. Use when designing or reviewing diagnostic, audit, planning, or evidence skills. The bundled auditor is advisory and read-only; it does not edit the package or decide user authority."
---

# Separate Review Evidence Effects

Find effect coupling in a skill contract without changing it.

## Run the advisory audit

Read [the audit rules](references/audit-rules.md), then run:

```bash
python3 scripts/audit_review_effects.py <skill-package>
```

The auditor scans `SKILL.md` and directly referenced Markdown for phrases that make persistence, collectors, probes, validation, mutation, Git, activation, or publication appear automatic from a review trigger. It emits line-located findings, the effect classes involved, and the rule that matched.

## Adjudicate findings

Treat each finding as a review lead. Explicit user-requested deliverables, narrowly declared automatic pipelines, and safe read-only inspection may be legitimate. Confirm the surrounding trigger, authority source, and stop boundary before proposing a change.

Use `--json` for machine-readable findings. A zero-finding result means only that no declared pattern matched; it does not prove the skill's authority semantics are sound. The script never edits, executes package helpers, stages, commits, installs, or activates anything.
