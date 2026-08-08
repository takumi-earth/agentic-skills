---
name: skill-researcher
description: "Research recurring agent behavior and skill opportunities from Codex and Claude JSONL conversation traces. Use when the user asks to inventory session logs, analyze instruction-following corrections or churn, compare harness behavior, discover or prioritize new user-level skills, refresh an earlier trace study, or build a bounded session-evidence bundle for a skill-review workflow. Do not use merely because a task uses skills, to perform the automatic post-goal review owned by `$auto-skill-enhancer`, or to create or edit skill packages owned by `$skill-creator`."
---

# Skill Researcher

Own trace evidence, research methodology, and skill-opportunity synthesis. Keep skill creation and post-goal enhancement as separate workflows.

## Preserve the research boundary

- Treat source JSONL files as immutable evidence. Do not edit, relocate, rename, normalize, redact in place, or delete them.
- Keep raw trace content out of generated inventories. Store only metadata, key shapes, counts, hashes, identifiers, and source line locations until contextual review is required.
- Treat keyword and correction signals as triage heuristics, never findings.
- Produce research artifacts and recommendations. Do not create or modify a skill unless the user separately authorizes implementation through `$skill-creator`.
- Let `$auto-skill-enhancer` own the automatic review of skills used in one completed goal. Supply its evidence extractor; do not absorb its approval or proposal workflow.
- Do not update memory, repositories, hooks, configuration, or external systems unless the user explicitly includes that mutation in scope.

## Choose the smallest research mode

- **Bounded Codex session:** Extract visible messages, goal events, tool/failure leads, and proven skill-use signals from one rollout with `scripts/extract_session_evidence.py`.
- **Context inspection:** Render compact user/assistant context around exact Codex or Claude JSONL lines with `scripts/trace_context.py`.
- **Corpus study:** Inventory one or both harness trees with `scripts/inventory_jsonl.py`, then group and balance conversation families with `scripts/partition_inventory.py`.
- **Refresh:** Re-run the deterministic scripts into a new study directory or pass `--replace` only after replacement is explicitly authorized, compare snapshot dates and counts, and preserve prior reports unless replacement was requested.

Do not scan a full corpus when a named session or a few exact evidence lines can answer the question.

## Define the study contract

Record before scanning:

- the research question and intended decision;
- included harness roots and time range;
- the domain selector, such as a path, CWD, repository family, or regular expression;
- whether the user wants an inventory, behavioral findings, candidate skills, enhancement evidence, or all four;
- the output directory and whether existing generated artifacts may be replaced;
- whether delegation was explicitly requested and the maximum workers per harness;
- excluded content, repositories, sessions, or artifact classes;
- the stopping condition.

Default a strict-ecosystem study to `~/.codex/skill-research/<study-name>/`. Use `*.ndjson` for generated row streams so later `*.jsonl` discovery cannot ingest the study itself.

## Build a privacy-preserving inventory

For a strict-ecosystem corpus:

```bash
python3 ~/agentic-skills/skill-researcher/scripts/inventory_jsonl.py \
  --root ~/.codex \
  --root ~/.claude \
  --output-dir ~/.codex/skill-research/<study-name> \
  --domain-regex '(?i)(?:/strict-rs(?:/|\b)|\bstrict\*|\bstrict-[a-z0-9-]+\b|\bstrict ecosystem\b)'
```

The inventory must:

- discover hidden and ignored `*.jsonl` files under the authorized roots;
- stream one file at a time rather than loading the corpus into memory;
- classify Codex and Claude trace categories and record structures;
- retain exact malformed-line locations while continuing past valid surrounding records;
- deduplicate repeated user text by content hash within each file;
- distinguish primary sessions from subagent traces where the format permits;
- record domain and correction-signal locations without copying message bodies, tool arguments, or tool output;
- exclude its own output directory.

Inspect `inventory-summary.md` and `schema-summary.json` before partitioning. Resolve schema defects rather than silently accepting incorrect session IDs, primary/subagent labels, or candidate counts.

## Group conversation families before analysis

Run:

```bash
python3 ~/agentic-skills/skill-researcher/scripts/partition_inventory.py \
  --inventory ~/.codex/skill-research/<study-name>/candidates.ndjson \
  --output-dir ~/.codex/skill-research/<study-name>/partitions \
  --partitions 6
```

Treat a primary conversation, continuations, full-history forks, and nested workers as one family whenever lineage evidence connects them. Do not count copied history or repeated assignment packets as independent corrections. Balance partitions deterministically by evidence volume and heuristic signal, not by file count alone.

## Read contextual evidence

Use inventory line leads to inspect the raw trace:

```bash
python3 ~/agentic-skills/skill-researcher/scripts/trace_context.py \
  /absolute/path/to/session.jsonl \
  --line 120,145 \
  --before 3 \
  --after 4
```

For a single completed Codex session, use:

```bash
python3 ~/agentic-skills/skill-researcher/scripts/extract_session_evidence.py \
  --transcript /absolute/path/to/rollout.jsonl
```

Read [research-protocol.md](references/research-protocol.md) before classifying corpus evidence, delegating partitions, or recommending a skill portfolio. Apply its false-positive controls and evidence schema exactly.

## Sample to saturation

Include:

- the largest or highest-churn families;
- high-signal families from different repositories, dates, and task modes;
- recent low-signal and clean controls;
- primary/subagent pairs where handoff behavior matters;
- both harnesses when making a cross-harness claim.

Stop only when later samples add no new material top-level pattern. Report the sample, stop condition, excluded evidence, and qualitative limitations. Do not present the study as a normalized prevalence estimate unless the design actually supports one.

## Delegate only with explicit authority

Do not launch research workers merely because partitions exist. When the user explicitly requests subagents or multi-agent analysis:

- assign disjoint family manifests and unique report paths;
- provide a self-contained packet even when full history is inherited;
- prohibit edits to source traces, inventories, skills, repositories, memory, and sibling reports;
- require a broad screen, a saturation sample, controls, exact citations, false-positive accounting, and a sole report artifact;
- keep final classification and cross-partition synthesis with the root researcher;
- close each wave before synthesizing or launching dependent validation.

## Synthesize skill opportunities

Promote a pattern only when contextual evidence establishes behavior, recurrence, and a stable corrective rule. Prefer direct user corrections, tool-proven boundary violations, repeated avoidable churn, and clean counterexamples over raw frequency.

For each candidate skill, provide:

- a concise name and semantic owner;
- the exact trigger context suitable for frontmatter;
- the degree of freedom;
- the repeated problem and evidence families;
- the smallest reinforcing contract;
- overlap with existing skills and the reason to merge, split, replace, or omit;
- realistic forward-test scenarios;
- limitations and evidence gaps.

Group patterns by trigger and responsibility rather than by diagnostic vocabulary. Prefer a compact foundation plus narrow task-mode skills when that reduces always-loaded context. Prefer no skill over a speculative, one-session, repository-accidental, or duplicative rule.

End by separating:

1. raw inventory and provenance;
2. contextual evidence and classifications;
3. cross-family synthesis;
4. recommended skill portfolio;
5. any later implementation request for `$skill-creator`.
