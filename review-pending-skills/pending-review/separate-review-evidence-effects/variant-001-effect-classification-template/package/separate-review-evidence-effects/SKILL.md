---
name: separate-review-evidence-effects
description: "Classify review, audit, planning, and diagnostic work into independent effect classes before acting. Use when a request or skill mentions inline analysis, persisted reports, collectors, probes, validation, remediation, Git persistence, or activation and could accidentally treat one as authority for another."
---

# Separate Review Evidence Effects

Map requested outcomes to exact effects instead of bundling them under `review`.

## Classify the surface

Read [the effect matrix](references/effect-matrix.md). Classify each proposed action as:

- read or inline analysis;
- persisted artifact creation;
- collector execution;
- probe or verification execution;
- source mutation;
- Git staging or persistence;
- promotion, installation, synchronization, or activation;
- publication or external communication.

Record the literal user instruction or controlling workflow authority for each effect. One authorized class does not imply another. A request to review usually authorizes relevant reads and an inline answer, not a scratch report, helper execution, remediation, commit, or activation.

## Preserve required deliverables

When the user explicitly requests a report file, generated ledger, validation run, or implementation, classify that exact effect as authorized and preserve its scope. Do not use effect separation to omit an intrinsic deliverable.

Stop only the unauthorized dependent effect. Continue any concrete, causally independent requested lane whose next action is already authorized. State remaining boundaries once without manufacturing optional evidence.
