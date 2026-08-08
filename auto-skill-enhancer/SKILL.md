---
name: auto-skill-enhancer
description: "Review the user-level skills actually used in a Codex conversation or goal against retained conversation or JSONL evidence, then propose precise, evidence-backed skill enhancements for user approval without editing any skill. Use automatically immediately after a successful `update_goal` call with `status: \"complete\"` when the goal-completion hook supplies the transcript path, or manually when the user requests a review of the current conversation, a full-history fork, or a named session. Manual use does not require a goal record, completed state, transcript path, or session ID. Do not use to apply already-approved enhancements."
---

# Auto Skill Enhancer

Treat a completed goal or explicitly selected conversation as an evaluation trace for the skills that guided it. Find transferable instruction, trigger, and tooling gaps; do not turn one session's incidental details into permanent policy. Consume researcher-owned evidence instead of implementing a parallel trace-research workflow.

## Preserve the automatic, manual, and review boundaries

- Keep the automatic trigger completion-only: run it only after successful goal-completion accounting.
- Allow an explicit manual invocation at any time, including during active work and from a full-history fork. Manual use does not require a goal, a completed goal, a completion hook, a transcript path, or a session ID, and it does not change goal state.
- Perform a read-only review. Do not edit skills, hook definitions, configuration, memory, repositories, or the transcript.
- Present proposals in the final response only. Do not create a proposal file unless the user requests one.
- Require explicit user approval before applying any proposal.
- Do not run project verification as part of this review. Session extraction and direct source inspection are analysis, not verification of the completed project.
- If the user later approves changes, use `$skill-creator` in that later turn to implement and validate them.
- Keep corpus inventory, JSONL schema research, conversation-family grouping, cross-harness sampling, and new-skill portfolio design in `$skill-researcher`.

## Preserve the automatic goal-completion handoff

For an automatic review, obey the completion hook's write-ahead protocol before reading this skill, extracting evidence, or performing review analysis. The write-ahead append is part of completing the goal, not part of the read-only review, and is the only automatic write this workflow permits.

- Use only the exact harness goal-file path validated and supplied by the hook.
- Draft the complete final-ready goal result that the user would receive if no post-goal hook had run. Preserve all material outcome, change, evidence, caveat, deferred-work, cleanup, and required goal-accounting details; exclude the skill review itself.
- Append that result exactly once between the hook-supplied delimiters without changing earlier goal content. Re-read the saved block and confirm it before beginning the review.
- If the block already exists for this goal, reuse it instead of appending another copy.
- If the exact file cannot be written and re-read, skip the automatic review and immediately deliver the ordinary goal-completion response from retained evidence.
- After the review, begin the final response with only the saved content between the delimiters, copied verbatim with its Markdown, whitespace, ordering, and nuance intact. Then add the skill review as a separate section; do not summarize, rewrite, or merge the preserved result into the review.
- After any context compaction, re-read the saved block from the harness goal file instead of reconstructing it from memory or the review evidence.

Do not create or modify a completion handoff during manual invocation.

## Build a bounded evidence bundle

Choose evidence according to the invocation:

- For the automatic completion hook, use the supplied transcript path and session ID.
- For a manual review of the current conversation or a full-history fork, use the retained visible conversation directly. Preserve the original chronology, and do not treat copied fork history as a new invocation, correction, or approval. Do not require the user to name a session ID or path, and do not guess that the newest rollout file is the current conversation. If the runtime exposes the exact current transcript, the extractor may supplement the retained history with line-number routing.
- For a named historical session, use the supplied exact transcript path or session ID.
- If a load-bearing turn is absent from retained history and no exact transcript is available, ask for that missing turn or evidence. Do not require a session ID as the only recovery path.

When an exact transcript path is available, run:

```bash
python3 ~/agentic-skills/skill-researcher/scripts/extract_session_evidence.py \
  --transcript /absolute/path/to/rollout.jsonl \
  --exclude-skill auto-skill-enhancer
```

For an explicit review that supplies only a session ID, run:

```bash
python3 ~/agentic-skills/skill-researcher/scripts/extract_session_evidence.py \
  --session-id 00000000-0000-0000-0000-000000000000 \
  --exclude-skill auto-skill-enhancer
```

For a manual current-conversation or full-history-fork review with no exact path or ID, continue from the retained visible turns without blocking on the extractor.

The extractor, when used:

- reads the rollout without modifying it;
- excludes reasoning, encrypted content, system messages, and developer messages;
- inventories visible user and assistant messages, goal events, tool counts, bounded failure candidates, and skill-use signals;
- distinguishes direct user-level skills from system skills and leaves packages outside the configured user skill root out of the enhancement shortlist;
- reports exact JSONL line numbers for follow-up inspection.

Treat its heuristics as routing aids, not conclusions. Inspect the raw JSONL around every load-bearing line before proposing a change, for example:

```bash
sed -n '120,145p' /absolute/path/to/rollout.jsonl
```

If the bundle is truncated, use its retained line numbers to inspect only the relevant raw records. Do not broaden into unrelated session-history research.

## Resolve the reviewed skill set

Review only skills that satisfy both conditions:

1. The session contains both a complete `SKILL.md` read and an invocation signal: an explicit user `$skill-name` invocation or an assistant declaration that the skill is being used.
2. The package is user-owned under `~/agentic-skills/<skill-name>/`.

Exclude:

- skills merely listed in injected catalogs;
- skills read only for comparison, research, creation, or inspection;
- skills mentioned only inside quoted or pasted material;
- `~/.codex/skills/.system/`;
- plugin-cache and repository-owned skills;
- `$auto-skill-enhancer` itself;
- a skill named in commentary but never read or otherwise used.

Read each eligible `SKILL.md` completely. Read `agents/openai.yaml` only when invocation behavior may need adjustment. Read a directly linked script or reference only when the suspected gap belongs to that resource.

## Diagnose before proposing

Compare the skill's intended contract with observable session behavior. Classify each material finding as one of:

- `instruction-gap`: required behavior was absent, ambiguous, misplaced, or too weak;
- `trigger-gap`: the skill under-triggered, over-triggered, or routed the wrong task phase;
- `resource-gap`: a bundled script or reference was missing, unreliable, or needlessly expensive;
- `conflict-or-duplication`: overlapping skills gave inconsistent or redundant direction;
- `execution-error`: the skill was adequate but the agent did not follow it;
- `not-a-skill-issue`: the cause belongs to task facts, repository policy, tooling, permissions, or a one-off user decision.

Use these standards:

- Prefer direct user corrections, rejected actions, repeated churn, unauthorized work, wrong completion claims, and avoidable tool failures over stylistic preferences.
- Distinguish live user feedback from pasted instructions, quoted prior dialogue, compaction summaries, subagent packets, and tool output.
- Require exact evidence from the raw JSONL or the retained visible turns. Cite JSONL line numbers when available; otherwise quote or uniquely identify the controlling visible turn. Do not infer a gap from memory or from the final answer alone.
- Do not blame a skill for behavior it explicitly prohibited.
- Prefer the narrowest semantic owner. Strengthen a shared foundation once instead of duplicating the same rule across every task-specific skill.
- Propose frontmatter changes only when the evidence concerns invocation or routing.
- Generalize behavior and decision rules; omit task-specific filenames, diagnostics, versions, and repository accidents unless they define the skill's stable domain.
- Prefer no change over a speculative, redundant, or overfit enhancement.

## Produce the review

Within the skill-review portion, lead with whether any change is warranted. Include every eligible used skill under either `Proposed changes` or `No change`.

For each proposal, provide:

- the skill name and absolute source path;
- exact transcript evidence with line numbers when available, or an unambiguous retained-turn citation otherwise;
- the finding classification and causal diagnosis;
- the smallest concrete edit, preferably as a focused unified diff;
- why the edit belongs in that skill rather than another owner;
- expected behavior and trigger impact;
- overfitting, duplication, or regression risk;
- a proportionate validation plan.

Keep proposal diffs limited to the lines needed to communicate the change. Do not silently include adjacent cleanup.

End with an explicit approval boundary such as:

```text
No skill files were changed. Tell me which proposals to apply; approved changes will be implemented and validated with `$skill-creator` in a separate turn.
```

If no eligible skill was used or no evidence-backed enhancement is warranted, say so directly and preserve the same no-change boundary.
