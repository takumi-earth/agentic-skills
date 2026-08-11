---
name: forward-test-skill-triggers
description: "Evaluate a new or materially changed skill in context-isolated agent runs without leaking the expected answer or prior diagnosis. Use after changing trigger frontmatter, default prompts, owner routing, or workflow semantics when inherited conversation history could hide under-triggering, over-triggering, or incorrect execution. Do not use this skill as authority to launch agents or mutate live systems."
---

# Forward-Test Skill Triggers

Separate whether a skill activates from whether it performs its contract correctly.

## Build an isolated evaluation

Read [the evaluation matrix](references/evaluation-matrix.md). Include at least:

- a direct `$skill-name` invocation;
- a realistic positive prompt that should trigger implicitly;
- the nearest negative prompt that should not trigger;
- a mixed-scope prompt with a neighboring owner;
- a prompt whose requested effect is not authorized.

Give each fresh agent only the skill package, the realistic prompt, and raw task artifacts it would normally receive. Do not disclose the intended answer, suspected defect, prior reviewer conclusions, or pass criteria through fixture names.

## Preserve effect authority

This skill designs and interprets evaluations; it does not authorize delegation, external calls, writes, or production effects. Launch fresh agents only when the caller separately authorizes that action. Replace live effects with inert fixtures unless the evaluation explicitly owns them.

## Score two independent dimensions

Record activation as `triggered`, `not-triggered`, or `ambiguous`. Record execution as `contract-satisfied`, `contract-violated`, or `not-exercised`. A correct answer produced without the intended skill does not prove trigger reachability, and a triggered skill that violates its workflow does not pass.

Preserve raw prompts, supplied artifacts, outputs, model and context mode, and any contamination finding. Treat structural validation and prompt rendering as prerequisites, not behavioral evidence.
