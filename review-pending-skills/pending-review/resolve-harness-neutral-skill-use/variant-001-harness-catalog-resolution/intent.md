# Harness-catalog resolution variant

## Concrete intent

Identify portable user-level skill references and body-read commands from Codex rollout evidence without hard-coding `~/.codex/skills` as the only runtime root.

## Approach

Consume an explicit available-skills catalog, scan only typed assistant messages and custom tool-call inputs, and report distinct evidence states for `$skill` references and exact `SKILL.md` path reads.

## Preserved nuance

A name reference, a read command, and faithful behavioral use are different claims. The script reports observations and never equates availability with use.

## Relationships and uncertainty

The likely resource owner is `$skill-researcher`. This candidate preserves the catalog-driven approach for review without automatically editing that official skill.

## Review questions

- Which rollout records should count as an explicit skill-use announcement?
- Should complete body-read proof be reconstructed from bounded range plans or left to a separate evidence classifier?
