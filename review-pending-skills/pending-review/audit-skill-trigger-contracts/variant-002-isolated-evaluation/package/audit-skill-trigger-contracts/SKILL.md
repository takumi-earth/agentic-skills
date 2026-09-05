---
name: audit-skill-trigger-contracts
description: "Audit skill entry paths and evaluate materially changed triggers, owner routing, or execution contracts. Use when explicit invocation is suppressed, metadata and body disagree, or isolated evaluation is requested or needed to assess a meaningful routing or workflow change. Do not apply to ordinary related work or treat an audit as authority to edit, enable, or invoke the target."
---

# Audit Skill Trigger Contracts

Choose the mode the task needs: inspect routing for an audit; load isolated evaluation mechanics when behavioral evidence is required. Structural validation alone does not prove activation or correct execution.

## Audit entry paths

Read the complete target `SKILL.md`, invocation-facing metadata, governing instructions, and relevant hook or harness configuration. Inspect without changing them unless implementation is separately authorized.

Distinguish direct conversational `$skill-name` invocation, direct harness or UI invocation, implicit task matching, automatic lifecycle invocation, inter-skill handoff, and ordinary related work that never invokes the skill. For each applicable path, record the trigger, retained inputs, exclusions, allowed effects, and these independent verdicts:

| Verdict | Required distinction |
| --- | --- |
| Package availability | `available`, `missing`, or `unusable` |
| Governing disablement | Whether higher authority disables invocation itself |
| Activation | Whether the entry path activates after governing policy is applied |
| Evidence prerequisite | `satisfied`, `missing`, or `not required` |
| Effect authority | Each read or inline finding, persisted report, collector, probe or validation, source change, Git operation, delegation, promotion, installation, synchronization, registration, trust, or external effect |
| Execution outcome | Successful effect, lawful no-op, failure, or not attempted |

Classify helpers by their actual effects: a read-only inventory may serve an authorized review, while a collector that writes evidence needs authority for that output. Trace authority to the user's instruction or a workflow the user authorized; an assistant-authored plan or a skill's own wording cannot supply a missing grant. Preserve explicitly requested reports, validation, and implementation without inferring permission for additional remediation, Git operations, activation, or publication.

Protect these boundaries:

- Explicit invocation requests that exact available skill unless higher authority disables invocation itself. Prohibiting one effect does not erase activation.
- Ordinary manual work differs from manually invoking an automatic skill. An exclusion for the former must not suppress the latter.
- A hook, transcript, handoff, session identifier, candidate bundle, or completed goal can supply evidence without becoming a prerequisite for direct invocation unless the user selected that requirement.
- `policy.allow_implicit_invocation: false` controls implicit selection. Keep it separate from explicit invocation and from effect authority.
- Missing evidence, a lawful no-op, a successful effect, and correct activation are different observations. Do not infer one from another.

Compare frontmatter, body, and default prompt. Recommend the exact affected field or passage and its expected positive and nearest-negative behavior. Preserve unrelated metadata and existing invocation policy. Load `$skill-creator` before authorized package edits.

## Evaluate changed behavior when needed

Read [the isolated evaluation procedure](references/isolated-evaluation.md) when fresh-context evidence is requested or inherited conclusions could mask a meaningful trigger or workflow defect. It defines realistic cases, evidence isolation, and independent activation and execution judgments.

For repeatable packets or collected-result checks, also read [the packet and result contract](references/packet-contract.md) before using `scripts/build_prompt_matrix.py`. The helper builds inert files and checks ledgers; it does not launch agents or determine semantic truth.

## Report the evidence and next action

For an audit, cover positive entry paths and nearest negatives relevant to the disputed behavior. Include explicit invocation with implicit selection disabled, higher-authority disablement of invocation, prohibition of only one effect, lifecycle invocation without a preassembled handoff, missing evidence after activation, lawful no-op behavior, ordinary related work, and an authorized effect where applicable.

For behavioral evaluation, report activation, execution, context contamination, and raw supporting evidence separately. Distinguish source review, written scenario walkthroughs, structural validation, direct helper tests, and actual independent evaluator runs.

A favorable verdict does not authorize implementation, promotion, synchronization, registration, trust, or execution. Preserve those effect boundaries and request only decisions that remain unresolved.
