---
name: auto-skill-creator
description: "Automatically materialize every potentially helpful user-level skill idea as design-preserving variants beneath `$review-pending-skills`, validate the complete invocation batch, and persist all complete candidate roots together in one creation-batch commit for collaborative review. Use after each goal ends and whenever invoked directly from a harness or conversation, including when the user already named candidates, packages, paths, or exact edits; no hook, handoff, prior approval, recurrence proof, or preassembled bundle is required. Reuse `$skill-creator` for draft mechanics and validation. Never auto-filter candidates, split one creation batch across commits, stage or commit a candidate descendant or unrelated path, mutate official skills, promote drafts, synchronize installations, register hooks, change configuration or memory, publish, or perform unrelated cleanup."
---

# Auto Skill Creator

Persist what may help before deciding whether it should become active guidance. Create complete, design-preserving pending variants and one creation-batch commit containing every complete candidate root from the invocation so the user can inspect, compare, repair, and converge them through `$review-pending-skills`; never collapse candidate creation into promotion or enablement.

## Activate without a candidate gate

- Run after each goal ends from retained conversation and goal evidence, even when no hook, enhancer handoff, researcher bundle, or preselected candidate exists.
- Run on every direct `$auto-skill-creator` invocation, whether it comes from the harness or conversation. A user-supplied candidate, target skill, package, source path, or exact edit narrows what to create; it never reroutes the task away from this skill.
- Treat `$auto-skill-enhancer` and `$skill-researcher` artifacts as optional structured evidence, not activation prerequisites or approval gates.
- Distinguish a raw mention from an idea the agent thinks may help, but once an idea is identified, materialize it. Do not invent catalog-derived candidates merely to make the run nonempty.
- Treat direct or post-goal invocation as authority only for bounded pending-artifact creation, validation, and Git persistence in the canonical repository. It authorizes one commit containing the complete `review-pending-skills/pending-review/<candidate-name>/` root for every candidate created or changed in that invocation. It never authorizes a narrower variant, package, script, or file pathspec, a partial invocation batch, or Git operations on pipeline owners, official skills, always-loaded guidance, unrelated work, promotion, installation, synchronization, linking, hook registration, configuration, memory, publication, or external systems.
- Use direct `$skill-creator` for ordinary user-selected official skill work only when `$auto-skill-creator` was not invoked and the task is not the automatic post-goal path.

## Retain every idea and approach

Use retained visible conversation, the exact living goal, a full-history fork, or supplied enhancer/researcher evidence. Preserve chronology and apply the newest controlling user correction.

- Do not reject creation because an idea is speculative, first-occurrence, apparently one-off, repository-specific, use-case-specific, overlapping, redundant, narrow, or not yet proven reusable.
- Do not require use-case-agnostic architecture. Persisting a concrete script or procedure makes later recurrence and comparison possible.
- Treat recurrence as evidence available only over time. Never claim ahead of time that the first or second occurrence will remain unique.
- Materialize every materially distinct implementation or instruction approach as its own variant. Preserve competing approaches even when one seems better or a convergence already looks likely.
- Treat overlap with an existing skill as relationship metadata. Do not assume the existing owner is complete, reliably trigger-reachable, authoritative at the required scope, or nuance-equivalent.
- Treat an explicit user-suggested idea as controlling candidate input. Preserve it even when it conflicts with the agent's current architectural preference.

If no potential skill idea is genuinely identifiable after reading the retained evidence, record that factual empty inventory in the scratch ledger and still report that the workflow ran. Do not manufacture an idea, but do not use absence of a preassembled bundle as a substitute for inspecting the evidence.

## Resolve the canonical repository and pending owner

Run `scripts/resolve_agentic_skills_repo.py` and require a checkout whose normalized Git remote identifies:

```text
https://github.com/takumi-earth/agentic-skills.git
```

Use the resolver's `selected.path` as the canonical source root and `scratchpad_root` for automatic-workflow ledgers and command evidence. Never write source packages into a harness installation.

Render repository paths relatively and paths beneath the user home as `~/...` in ledgers, metadata, prompts, reports, and command examples. A resolver or filesystem API may expand `~` transiently for I/O, but normalize it before serialization or presentation; never persist the expanded home prefix as candidate evidence.

Require the canonical package `<selected.path>/review-pending-skills` and its `pending-review/` store. That top-level package owns candidate persistence and review. Do not fall back to placing a candidate directly under the canonical repository or a harness skill root when the pending owner is missing; report the affected local stop and continue any independent candidate analysis.

## Freeze an append-only creation ledger

Before creating variants, persist a new task ledger beneath `<scratchpad-root>/auto-skill-creator/<run-id>/`. Never overwrite a prior run or variant record. Include:

- invocation authority and retained evidence scope;
- every identified candidate idea without selected/rejected classification;
- every materially distinct proposed variant and its concrete intent;
- candidate and variant identifiers, predecessors, repository specificity, uncertainties, and relationships to existing skills;
- the resolved canonical repository and pending-store paths;
- exact source allowlists and excluded official or external effects;
- draft resources and validation planned for each variant.

Descriptive labels preserve review context; they do not authorize filtering. Persist the complete initial invocation in one creation-batch commit before beginning any later edit. Before that later work, append a ledger entry classifying whether it preserves or changes the variant's declared design identity. A change of intent, approach, authority boundary, or activation effects creates a sibling variant and records its predecessors. A correctness repair that restores the behavior already declared by `intent.md`, `review.json`, and the draft contract updates the same variant and records the defect, repair, validation, and later invocation-batch commit without rewriting the earlier ledger.

Keep run evidence separate from reusable candidate resources:

- Leave concrete investigation evidence, raw conversation context, memory context, source context, diagnostic output, and append-only run records beneath the resolver-selected `.scratchpad/` run. Those are evidence instances, not draft package resources.
- Put reusable JSON schemas, schema-producing or schema-consuming product scripts, reusable instructions, and references inside the variant that owns them. Do not use a multi-candidate scratch directory as their long-term source location.
- When a handoff already placed a reusable schema or product resource in scratch, declare one source-to-destination move manifest, create every owning pending variant directory first, then move each declared resource exactly once. Do not copy the whole run tree, leave a duplicate original, or move the run-specific evidence instances merely because a candidate owns their schema.
- Give a resource shared by several candidates one canonical owning variant and record explicit relationships from the consumers. Do not create a non-candidate shared directory directly beneath `pending-review/` or duplicate the resource to evade ownership.

## Materialize design-preserving pending variants

Use this layout for every approach:

```text
review-pending-skills/pending-review/<candidate-name>/<variant-id>/
  intent.md
  review.json
  package/<candidate-name>/SKILL.md
  package/<candidate-name>/agents/openai.yaml
```

- Choose a short lowercase hyphen-case `<candidate-name>` that describes the concrete capability. Do not rename it merely to sound more generic.
- Choose the next unused lowercase hyphen-case `<variant-id>`, such as `variant-001-script-notebook`. Never reuse or overwrite an existing variant directory.
- Use `$skill-creator` initialization beneath the variant's `package/` directory so the nested `<candidate-name>` is a complete validator-ready draft package. Add scripts, references, or assets when that approach needs them, and test every executable path directly.
- Write `intent.md` with the concrete use, approach, preserved nuance, differences from other variants or official skills, uncertainty, and questions for review. Record externalized design rationale, not private hidden reasoning.
- Write `review.json` with schema version `1`, matching `candidate_name` and `variant_id`, status `pending`, string-list `predecessors`, string-list `provenance`, relationship objects, and string-list `activation_effects`.
- A revision, alternative, or convergence that changes declared intent, approach, authority, or activation effects creates a new sibling variant. List predecessor variant paths and keep every predecessor intact. A correctness repair that preserves those declared fields updates the same variant; do not invent a false sibling merely because executable or metadata bytes changed.
- Never edit an official top-level skill as an automatic candidate outcome. A possible enhancement to an existing skill is represented by a complete pending variant plus relationship metadata for later merge review.

## Guard pending source scope

Before source creation, run `scripts/skill_change_guard.py snapshot` for the existing `review-pending-skills` package and any pipeline package the current user explicitly authorized for direct maintenance. Write the snapshot below the resolver-selected `.scratchpad/` task directory.

Immediately before live creation, run `scripts/skill_change_guard.py unchanged`. After creation and validation, run `scripts/skill_change_guard.py verify` with every intended pending-variant path explicitly allowlisted. Treat an unexpected official-package change as a failure. Never clean, restore, stage, commit, or rewrite unrelated packages; the only Git mutation owned below is one invocation-batch commit containing every complete pending-candidate root created or changed by that invocation.

The guard proves filesystem scope only. The evidence ledger proves that every idea and approach was retained; `$skill-creator` proves draft structure; `$review-pending-skills` owns collaborative disposition; and separate user authority owns promotion and enablement.

## Validate and commit without promoting

For every created variant:

1. Run direct tests for every added script.
2. Run the canonical structural validator on the complete nested draft package.
3. Run `review-pending-skills/scripts/pending_skill_inventory.py` and confirm the variant appears with its distinct hashes and relationships.
4. Exercise positive creation and negative activation boundaries locally. Use subagents only when the user separately authorizes delegation.
5. Verify selected filesystem scope and prove the candidate is not a top-level package or harness projection.

After every variant for every candidate in the invocation passes creation validation, persist the whole invocation as one Git batch while keeping each candidate root indivisible:

1. Build the repository-relative path set from every complete `review-pending-skills/pending-review/<candidate-name>/` root created or changed in the invocation. Never substitute a `<variant-id>/`, `package/`, `scripts/`, filename, glob, `.`, repository-wide path, or only a subset of the invocation's candidates.
2. Inspect the existing index before staging. If it contains any path outside that complete candidate-root set, preserve it and stop the invocation's commit lane; do not unstage, absorb, bypass, or split the batch around unrelated staged work. Continue independent candidate analysis and validation.
3. Stage every complete candidate root together with one path-bounded `git add -- <candidate-root>...` invocation.
4. Read [the staged-object contract](references/staged-object-contract.md), then run `scripts/manage_creation_batch.py create` with the persisted inventory, every complete candidate root, every validation report, and a new immutable manifest path beneath this run's `.scratchpad/auto-skill-creator/<run-id>/`. This snapshots exact staged pathnames, blob bytes, executable modes, symlink targets, evidence hashes, and the precommit OID. Refuse an unrelated staged path, a root without staged transition coverage, or any untracked or unstaged candidate remainder.
5. Immediately before the commit, run `scripts/manage_creation_batch.py verify-precommit` against that immutable manifest. Require status `success`; do not commit, narrow the pathspec, rewrite the manifest, or fragment the batch when `HEAD`, evidence, index objects, or candidate remainder differs.
6. Commit the complete invocation batch once using the repository's commit convention. Staging and committing remain explicit caller-owned effects; `manage_creation_batch.py` only inspects state and persists evidence. Use a creation subject for the initial durable snapshot and a correctness or revision subject for a later batch. The initial creation-batch commit must exist before any later edit to its candidates begins. A commit records candidate persistence, not promotion or enablement.
7. Run `scripts/manage_creation_batch.py record-postcommit` with the same manifest and an append-only result JSONL path. Require exactly one commit transition, every declared root and no unrelated transition path, and committed tree parity with the staged-object snapshot. Record the precommit and resulting commit OIDs without editing candidate metadata.

The helper exposes exactly these subcommands:

```bash
python3 scripts/manage_creation_batch.py create \
  --repo <resolved-repo> \
  --inventory <inventory.json> \
  --candidate-root review-pending-skills/pending-review/<candidate-name> \
  --validation-report <validation-report.json> \
  --output <immutable-manifest.json>

python3 scripts/manage_creation_batch.py verify-precommit \
  --repo <resolved-repo> \
  --manifest <immutable-manifest.json>

python3 scripts/manage_creation_batch.py record-postcommit \
  --repo <resolved-repo> \
  --manifest <immutable-manifest.json> \
  --result <append-only-result.jsonl>
```

Run `python3 scripts/manage_creation_batch.py --self-test` after changing the helper. The packaged `references/creation-batch.schema.json` and `references/creation-batch-result.schema.json` document its manifest and result shapes; the helper's internal validation remains authoritative at runtime.

For later work, first require the initial creation-batch commit, then compare every proposed change with each affected variant's declared design fields. If a correction restores an existing contract, update that variant and rerun every affected direct and structural test. If it changes the design, create and validate a sibling variant. Group every complete candidate root touched by that follow-up invocation into one later commit rather than producing per-candidate or per-variant commits. Git history owns the evolution of a variant's correctness; sibling directories own materially different designs.

## Hand every artifact to review

Report every created candidate and variant, its exact pending path, intent, provenance, relationships, validation, the single invocation-batch commit identifier and all complete candidate roots it contains, and possible activation effects. Invoke `$review-pending-skills` for comparison only when it is separately installed and enabled; otherwise report its canonical source path and apply no installation or synchronization as a workaround. Do not ask the user to approve ideas before persisting them, and do not promote, merge, delete, synchronize, or enable anything as part of automatic creation.
