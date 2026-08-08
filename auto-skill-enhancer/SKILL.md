---
name: auto-skill-enhancer
description: "Analyze a conversation or goal for every potentially helpful user-level skill idea and materially distinct approach, persist their evidence and uncertainty without candidate filtering, and always hand the complete inventory plus candidate-root Git boundary to `$auto-skill-creator` for design-preserving pending creation. Use automatically after successful goal completion when the hook supplies the transcript, or manually when the user requests automatic skill enhancement from current, forked, or named-session evidence. Remain read-only with respect to canonical skill source and Git state; do not promote or enable candidates or use for user-selected manual official-skill implementation."
---

# Auto Skill Enhancer

Treat a completed goal or explicitly selected conversation as a source of candidate ideas, alternative approaches, concrete scripts, and possible instruction, trigger, or tooling gaps. Preserve speculation, first occurrences, repository-specific details, use-case specificity, and overlap as review context rather than filtering them before the user can inspect them. Consume researcher-owned evidence instead of implementing a parallel trace-research workflow, then hand the complete unapproved inventory and complete-candidate-root commit requirement to `$auto-skill-creator` for design-preserving pending creation.

## Preserve analysis and implementation ownership

- Keep the automatic trigger completion-only: run it only after successful goal-completion accounting.
- Allow an explicit manual invocation at any time, including during active work and from a full-history fork. Manual use does not require a goal, a completed goal, a completion hook, a transcript path, or a session ID, and it does not change goal state.
- Keep this skill's evidence analysis read-only. Do not edit skills, hook definitions, configuration, memory, repositories, or the transcript directly.
- Persist the evidence and complete candidate inventory under the resolved canonical repository's `.scratchpad/auto-skill-enhancer/<run-id>/`; do not leave it only in conversation output.
- Hand every persisted inventory to `$auto-skill-creator` immediately, including an empty inventory. The creator independently inspects retained evidence, materializes every idea it identifies as design-preserving pending variants, and owns validation plus complete-candidate-root creation or correctness commits; absence of a preselected candidate is not an activation gate.
- Do not run project verification as part of this review. Session extraction and direct source inspection are analysis, not verification of the completed project.
- Let `$auto-skill-creator` materialize every identified idea and materially distinct approach beneath `$review-pending-skills` and reuse `$skill-creator` internally for draft package mechanics. Reserve direct `$skill-creator` use for user-selected official-skill work that does not invoke the automatic path.
- Keep corpus inventory, JSONL schema research, conversation-family grouping, cross-harness sampling, and new-skill portfolio design in `$skill-researcher`.

## Preserve the automatic goal-completion handoff

For an automatic review, obey the completion hook's write-ahead protocol before reading this skill, extracting evidence, or performing review analysis. The write-ahead append is part of completing the goal, not part of the read-only review, and is the only automatic write this workflow permits.

- Use only the exact harness goal-file path validated and supplied by the hook.
- Draft the complete final-ready goal result that the user would receive if no post-goal hook had run. Preserve all material outcome, change, evidence, caveat, deferred-work, cleanup, and required goal-accounting details; exclude the skill review itself.
- Append that result exactly once between the hook-supplied delimiters without changing earlier goal content. Re-read the saved block and confirm it before beginning the review.
- If the block already exists for this goal, reuse it instead of appending another copy.
- If the exact file cannot be written and re-read, skip the automatic review and immediately deliver the ordinary goal-completion response from retained evidence.
- After analysis and the automatic-creator handoff, begin the final response with only the saved content between the delimiters, copied verbatim with its Markdown, whitespace, ordering, and nuance intact. Then add the automatic skill-maintenance result as a separate section; do not summarize, rewrite, or merge the preserved result into it.
- After any context compaction, re-read the saved block from the harness goal file instead of reconstructing it from memory or the review evidence.

Do not create or modify a completion handoff during manual invocation.

## Build a bounded evidence bundle

Choose evidence according to the invocation:

- For the automatic completion hook, use the supplied transcript path and session ID.
- For a manual review of the current conversation or a full-history fork, use the retained visible conversation directly. Preserve the original chronology, and do not treat copied fork history as a new invocation, correction, or approval. Do not require the user to name a session ID or path, and do not guess that the newest rollout file is the current conversation. If the runtime exposes the exact current transcript, the extractor may supplement the retained history with line-number routing.
- For a named historical session, use the supplied exact transcript path or session ID.
- If a load-bearing turn is absent from retained history and no exact transcript is available, ask for that missing turn or evidence. Do not require a session ID as the only recovery path.

Resolve the canonical skill repository first by running the packaged `auto-skill-creator/scripts/resolve_agentic_skills_repo.py`. Use its `selected.path` for source reads and its `scratchpad_root` for every generated report, excerpt, and candidate bundle. When several canonical checkouts exist, the resolver's smallest-distance-to-home selection is controlling.

Render repository paths relatively and paths beneath the user home as `~/...` in inventories, excerpts, prompts, reports, and command examples. Filesystem tools may expand `~` transiently for I/O, but normalize it before serialization or presentation; never persist the expanded home prefix in evidence handed to the creator.

When an exact transcript path is available, capture the extractor through the packaged audit driver:

```bash
python3 <resolved-repo>/filesystem-git-observability/scripts/persist_command_report.py \
  --output <scratchpad-root>/auto-skill-enhancer/<run-id>/session-evidence.json \
  --purpose extract-session-evidence \
  --input ~/path/to/rollout.jsonl \
  --parse-json \
  -- python3 <resolved-repo>/skill-researcher/scripts/extract_session_evidence.py \
    --transcript ~/path/to/rollout.jsonl \
    --exclude-skill auto-skill-enhancer
```

For an explicit review that supplies only a session ID, run:

```bash
python3 <resolved-repo>/filesystem-git-observability/scripts/persist_command_report.py \
  --output <scratchpad-root>/auto-skill-enhancer/<run-id>/session-evidence.json \
  --purpose extract-session-evidence \
  --parse-json \
  -- python3 <resolved-repo>/skill-researcher/scripts/extract_session_evidence.py \
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

Treat its heuristics as routing aids, not conclusions. Inspect the raw JSONL around every load-bearing line with the packaged durable context reader, for example:

```bash
python3 <resolved-repo>/filesystem-git-observability/scripts/inspect_source_context.py \
  --source ~/path/to/rollout.jsonl \
  --output <scratchpad-root>/auto-skill-enhancer/<run-id>/line-133-context.txt \
  --line 133 \
  --context 12
```

If the bundle is truncated, use its retained line numbers to inspect only the relevant raw records. Do not broaden into unrelated session-history research.

## Inventory potential skill ideas without pruning

Use actually invoked user-level skills as one high-value evidence set, not as an eligibility gate for candidate creation. Also retain possible new skills, concrete scripts worth persisting, trigger or authority rules that may belong above an optional skill, alternative approaches, repository-specific helpers, and relationships to system, plugin, or repository-owned guidance.

- Distinguish raw catalog listings, quoted names, and incidental mentions from an idea the agent actually thinks may help. Do not fabricate candidates from names alone.
- Once an idea is identified, keep it in the inventory even when no current user-level skill was invoked, the proposed owner is uncertain, the evidence is speculative, or an existing skill appears to overlap.
- Read every current user-level skill that may be an owner or overlap completely before describing that relationship. Read `agents/openai.yaml` when invocation behavior is relevant and directly linked scripts or references when the idea concerns them.
- Treat `.system`, plugin-cache, and repository-owned skills as comparison evidence rather than automatic mutation targets. A pending user-level candidate may still record how it overlaps or differs.
- Keep `$auto-skill-enhancer` itself out of its own candidate inventory unless the retained user correction explicitly concerns this skill, as it does in the current maintenance task.

## Describe candidates without filtering

Compare the skill's intended contract with observable session behavior. Classify each material finding as one of:

- `instruction-gap`: required behavior was absent, ambiguous, misplaced, or too weak;
- `trigger-gap`: the skill under-triggered, over-triggered, or routed the wrong task phase;
- `resource-gap`: a bundled script or reference was missing, unreliable, or needlessly expensive;
- `conflict-or-duplication`: overlapping skills gave inconsistent or redundant direction;
- `execution-error`: the skill was adequate but the agent did not follow it;
- `not-a-skill-issue`: the cause belongs to task facts, repository policy, tooling, permissions, or a one-off user decision.

Use these standards:

- Give direct user corrections, rejected actions, repeated churn, unauthorized work, wrong completion claims, and avoidable tool failures prominent provenance, while retaining stylistic, speculative, and alternative-design ideas when the agent thinks they may help.
- Distinguish live user feedback from pasted instructions, quoted prior dialogue, compaction summaries, subagent packets, memory, and tool output. Record the source class so review can weigh it; do not use the class to suppress creation.
- Cite exact raw JSONL lines when available or uniquely identify retained visible turns. When an idea is an inference or speculation rather than an observed gap, label that explicitly instead of inventing supporting evidence.
- Record when a skill explicitly prohibited the observed behavior. That may make the issue an execution error while still leaving a trigger, always-loaded routing, mechanical safeguard, or alternative skill candidate worth reviewing.
- Describe the narrowest apparent semantic owner and every plausible alternative owner. Do not merge or reject candidates before review merely because one shared foundation looks attractive.
- Record frontmatter implications when the idea concerns invocation or routing.
- Preserve task-specific filenames, diagnostics, versions, repository circumstances, and concrete scripts when they carry the use that made the idea worth persisting. Generalization is an optional later review outcome, not a creation prerequisite.

## Persist and hand off the complete inventory

Persist one append-only inventory beneath `.scratchpad/auto-skill-enhancer/<run-id>/`. Include every identified idea and materially distinct approach; do not classify candidates into accepted and rejected sets. If the analysis identifies no idea, persist an explicit empty inventory without pretending the workflow did not run.

For each candidate, provide:

- the proposed candidate name, concrete capability, and whether it is a new pending skill, a possible relationship to an existing owner, or both;
- exact transcript evidence with line numbers when available, or an unambiguous retained-turn citation otherwise;
- the finding classification and causal diagnosis;
- every materially distinct proposed approach and the complete draft behavior, script, reference, asset, or instruction resource each approach may need; do not require an existing source file or reduce a new candidate to a focused diff;
- why the idea may help and every plausible owner or relationship; do not decide that one existing owner eliminates the candidate;
- expected behavior and trigger impact;
- overfitting, duplication, or regression risk;
- a proportionate validation plan;
- the required Git handoff: after validation, `$auto-skill-creator` stages and commits the entire `review-pending-skills/pending-review/<candidate-name>/` root for creation and for any later same-design correctness repair, never a descendant path.

When a focused diff helps explain an approach, include it as supporting material rather than a candidate gate or required form. Preserve concrete implementation context and do not silently include adjacent cleanup.

After persisting and re-reading the inventory, always invoke `$auto-skill-creator` with its exact path and evidence scope. The enhancer owns evidence description and performs no source or Git mutation; the creator owns design-preserving pending materialization, validation, and complete-candidate-root commits; `$review-pending-skills` and the user own comparison and disposition. Neither automatic skill may reject, merge, promote, synchronize, or enable a candidate.

The final maintenance summary must report the enhancer inventory, every creator-produced pending candidate and variant, any truly empty result after independent retained-evidence inspection, exact validation, each complete candidate-root commit, and the fact that no candidate was enabled. It may invite collaborative review, but it must not ask the user to pre-approve candidate creation that has already been authorized.
