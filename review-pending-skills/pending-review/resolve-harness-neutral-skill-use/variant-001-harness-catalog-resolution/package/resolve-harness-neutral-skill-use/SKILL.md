---
name: resolve-harness-neutral-skill-use
description: "Resolve skill-use evidence from an explicit harness available-skills catalog and typed Codex rollout records. Use when session analysis must distinguish skill availability, explicit $skill references, and SKILL.md read commands across harness roots without assuming ~/.codex/skills owns every user-level package."
---

# Resolve Harness-Neutral Skill Use

Start from the harness catalog supplied in the session. Do not discover skill roots by scanning the user's home directory.

## Prepare catalog evidence

Provide JSON:

```json
{"skills":[{"name":"guard-strict-work","path":"~/.agents/skills/guard-strict-work/SKILL.md"}]}
```

Run:

```bash
python3 scripts/resolve_catalog_skill_use.py --catalog <catalog.json> --transcript <rollout.jsonl>
```

The script reads typed `response_item` records and reports:

- `assistant_reference`: an assistant message explicitly named `$skill`;
- `body_read_command`: a custom tool call contained the catalog's exact `SKILL.md` path and a read-oriented command;
- source line numbers for both observations.

Do not label a skill behaviorally used merely because it was available, mentioned in quoted guidance, or read. Evaluate faithful use separately from the task effects.

## Preserve scope

Accept only catalog entries supplied by the caller. Normalize paths beneath the home directory to `~/...` in output. Do not follow unrelated directories, synchronize installations, or mutate a skill.

Validate copied and symlinked catalog paths, an assistant reference without a body read, a body read without a reference, developer text that lists skills but is not an assistant use announcement, and an unknown `$name`.
