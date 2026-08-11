---
name: audit-skill-trigger-contracts
description: "Audit a skill's explicit conversational invocation, explicit harness invocation, implicit task matching, automatic lifecycle trigger, and inter-skill handoff as distinct entry paths. Use when a manual or automatic call is being suppressed by an exclusion, metadata and body disagree, or a valid entry path is incorrectly treated as a prerequisite for another. Do not use this audit as authority to edit, install, enable, or invoke the target skill."
---

# Audit Skill Trigger Contracts

Build an entry-path matrix before changing skill routing. Separate whether a package is available, whether higher authority disables it, whether it activates, what evidence it requires, which effects activation authorizes, and what execution actually does.

## Keep audit and implementation separate

- Inspect the complete target `SKILL.md`, invocation-facing metadata, governing instructions, and relevant hook or harness configuration without modifying them.
- Recommend exact frontmatter, body, metadata, hook, or test changes. Name the affected field or passage and the expected positive and nearest-negative behavior.
- Apply those recommendations only when the user separately authorizes implementation. Load `$skill-creator` before editing a skill package and preserve promotion, synchronization, registration, trust, and invocation as separate effects.
- Never treat a favorable audit verdict as implementation or activation authority.

## Enumerate every entry path

For the target skill, record:

- direct `$skill-name` invocation in conversation;
- direct harness or UI invocation;
- implicit invocation because the current task matches frontmatter;
- automatic lifecycle invocation such as goal completion or turn end;
- handoff from another skill, hook, or retained evidence bundle;
- ordinary related work where the skill itself was not invoked.

For each path, record the trigger source, required retained inputs, allowed effects, exclusions, and expected positive and negative scenarios. Issue these verdicts independently:

| Verdict | Required distinction |
| --- | --- |
| Package availability | Record `available`, `missing`, or `unusable`; do not call an unavailable package an activation failure. |
| Governing disablement | Record whether higher-authority instructions or harness policy disable invocation of the skill itself. Keep that separate from a prohibition on one effect. |
| Activation | Record whether an explicit request, implicit match, lifecycle event, or handoff activated the skill after governing policy was applied. |
| Evidence prerequisite | Record `satisfied`, `missing`, or `not required`; do not turn a useful input into an activation prerequisite. |
| Effect authority | Record each requested read, write, configuration, registration, synchronization, trust, or external effect as separately authorized or unauthorized. |
| Execution outcome | Record `successful side effect`, `lawful no-op`, `failed`, or `not attempted`; none of these outcomes retroactively proves or disproves activation. |

## Protect explicit invocation

- A direct `$skill-name` invocation requests that exact available skill. It activates unless the package is missing or unusable, or a higher-authority instruction or harness policy explicitly disables invocation of the skill itself. A prohibition on one requested effect does not erase activation; record that effect as unauthorized and the outcome as a lawful no-op or diagnostic. Do not let a lower-authority body clause route away from a skill after its frontmatter already triggered.
- An exclusion for ordinary manual work does not exclude manual invocation of the automatic skill itself. Phrase the distinction using the exact invoked skill, not the ambiguous word `manual` alone.
- A hook, handoff, transcript, session identifier, candidate bundle, or completed goal may supply evidence without becoming a prerequisite for direct invocation unless the user selected that requirement.
- `policy.allow_implicit_invocation: false` controls implicit discovery only. Keep it distinct from explicit `$skill-name` invocation, which remains available unless package availability or higher authority says otherwise.
- A skill may activate and then lawfully do nothing because no requested effect is authorized, a required evidence input is missing, or its positive condition is absent. Report that state as activation plus a no-op or diagnostic, not as suppressed activation.
- A successful side effect proves only that an effect occurred. It does not prove that the package was properly activated, that prerequisites were satisfied, or that the effect was authorized.

## Align metadata and body

Read the complete `SKILL.md` and invocation-facing metadata. Verify that frontmatter states every valid trigger and that the body cannot silently narrow those triggers. Recommend exact OpenAI metadata changes when the default prompt or implicit policy would demonstrate the old behavior; apply them only in a separately authorized `$skill-creator` implementation phase.

## Test the matrix

Exercise every positive entry path and its nearest negative control. Include direct invocation plus an exact user-selected target, explicit invocation while implicit invocation is disabled, higher-authority disablement of the skill, higher-authority prohibition of only one effect, automatic invocation without a preassembled handoff, missing evidence after valid activation, a lawful no-op, related work that never invokes the skill, an unauthorized effect, and a successful authorized effect. Report package availability, governing disablement, activation, evidence prerequisites, effect authority, and execution outcome separately.
