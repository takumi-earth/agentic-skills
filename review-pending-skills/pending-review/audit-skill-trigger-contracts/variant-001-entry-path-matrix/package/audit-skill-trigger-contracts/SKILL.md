---
name: audit-skill-trigger-contracts
description: "Audit a skill's explicit conversational invocation, explicit harness invocation, implicit task matching, automatic lifecycle trigger, and inter-skill handoff as distinct entry paths. Use when a manual or automatic call is being suppressed by an exclusion, metadata and body disagree, or a valid entry path is incorrectly treated as a prerequisite for another."
---

# Audit Skill Trigger Contracts

Build an entry-path matrix before changing skill routing. Separate whether a skill activates from what evidence it consumes and which effects activation authorizes.

## Enumerate every entry path

For the target skill, record:

- direct `$skill-name` invocation in conversation;
- direct harness or UI invocation;
- implicit invocation because the current task matches frontmatter;
- automatic lifecycle invocation such as goal completion or turn end;
- handoff from another skill, hook, or retained evidence bundle;
- ordinary related work where the skill itself was not invoked.

For each path, record the trigger source, required retained inputs, allowed effects, exclusions, and expected positive and negative scenarios.

## Protect explicit invocation

- A direct invocation of the skill always activates it unless a higher-authority instruction explicitly forbids the entire operation. Do not let a body clause route away from a skill after its frontmatter already triggered.
- An exclusion for ordinary manual work does not exclude manual invocation of the automatic skill itself. Phrase the distinction using the exact invoked skill, not the ambiguous word `manual` alone.
- A hook, handoff, transcript, session identifier, candidate bundle, or completed goal may supply evidence without becoming a prerequisite for direct invocation unless the user selected that requirement.
- Implicit-invocation policy controls automatic discovery, not whether explicit `$skill-name` invocation works.

## Align metadata and body

Read the complete `SKILL.md` and invocation-facing metadata. Verify that frontmatter states every valid trigger and that the body cannot silently narrow those triggers. Update OpenAI metadata when the default prompt or implicit policy would demonstrate the old behavior.

## Test the matrix

Exercise every positive entry path and its nearest negative control. Include direct invocation plus an exact user-selected target, automatic invocation without a preassembled handoff, related work that never invokes the skill, and an effect that activation still does not authorize. Report activation and authorization separately.
