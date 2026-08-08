---
name: review-pending-skills
description: "Review design-preserving candidate skill variants and their candidate-root Git evolution beneath this package's `pending-review/` directory. Use when the user wants to inspect, compare, correct, revise, converge, retain, reject, merge, promote, or prepare activation of automatically created skill ideas. Preserve every materially distinct design, treat same-design correctness repairs as later commits to the same variant, require the complete candidate folder as the minimum commit unit, and keep review, promotion, and enablement separate; do not auto-filter candidates, silently mutate official skills, delete history, synchronize installations, or register hooks."
---

# Review Pending Skills

Treat `pending-review/` plus its Git history as a durable design and implementation notebook, not a deployment queue that the agent may prune. Read every relevant candidate and variant completely, inspect its candidate-wide evolution, preserve concrete intent and use-case specificity, and leave the final disposition to the user.

Render candidate paths relatively and paths beneath the user home as `~/...` in review packets, prompts, ledgers, and commands shown to the user. Filesystem code may expand `~` transiently for I/O, but normalize it before serialization or presentation; never persist the expanded home prefix in review evidence.

## Inventory the pending store

Run the package-owned read-only inventory before review:

```bash
python3 scripts/pending_skill_inventory.py
```

The script resolves this package's own `pending-review/` directory, rejects escaping symlinks and malformed variant layouts, hashes required files, and emits deterministic JSON. It never writes candidate state.

Each design-preserving variant has this layout:

```text
pending-review/<candidate-name>/<variant-id>/
  intent.md
  review.json
  package/<candidate-name>/SKILL.md
  package/<candidate-name>/agents/openai.yaml
```

Read `intent.md`, `review.json`, the complete draft `SKILL.md`, and its OpenAI metadata for every variant in scope. Read directly referenced draft scripts, references, or assets when present. Do not infer the candidate from its directory name or inventory summary alone.

## Preserve designs and correctness evolution

- Never suppress or remove a candidate because it appears speculative, first-occurrence, repository-specific, use-case-specific, overlapping, or redundant. Those are review observations, not creation or deletion authority.
- Do not require a candidate to be use-case agnostic. Persisting a concrete script or procedure can be valuable before recurrence or generality is known.
- Treat materially different approaches as separate design variants. A second or twenty-fifth approach remains useful evidence even when a later design appears stronger.
- Classify a proposed change against the variant's declared `intent.md`, `review.json`, skill contract, authority boundary, and activation effects. A change to intent, approach, authority, or activation effects creates a new sibling `<variant-id>` with predecessor relationships recorded in `review.json`; preserve every source variant.
- Treat a script, metadata, documentation, or contract correction that restores already-declared behavior as evolution of the same variant. Update that variant, revalidate it, and record the repair in a later Git commit; do not manufacture a sibling that falsely suggests a distinct design.
- Keep both storage layers reconstructable. Current variant files own the complete present design and predecessor relationships; candidate-root Git history owns creation and correctness evolution. Never rely on history to recover an overwritten design alternative, and never hide a same-design repair in an uncommitted rewrite.

## Review complete candidate-root history

Use `pending-review/<candidate-name>/` as the minimum history and commit scope. Never narrow review or mutation to one `<variant-id>/`, nested `package/`, `scripts/`, or filename merely because the visible change appears local.

- Inspect read-only Git history for the complete candidate root, including its creation commit and later correctness or sibling-variant commits. Review the whole candidate state at each relevant checkpoint so unchanged sibling context remains visible alongside the diff.
- Confirm that current intent, metadata, packages, and resources agree with the recorded evolution. If a candidate-root change remains uncommitted, report that gap; do not silently treat the working tree as durable history.
- When creating a requested sibling or applying an authorized correctness repair, validate first, inspect the existing index, then stage the complete `review-pending-skills/pending-review/<candidate-name>/` root. Never stage a descendant path. If unrelated paths are already staged, preserve them and stop only this commit lane rather than unstaging or absorbing them.
- Before committing, require every staged path to be inside that one candidate root and no untracked or unstaged change to remain inside it. Commit one candidate root at a time under the repository's commit convention, then record the commit identifier in append-only scratch evidence rather than editing the candidate solely to store its own hash.
- A candidate-root commit is persistence for review. It does not promote the nested package, install it, synchronize it, register a hook, change configuration, or activate its invocation policy.

## Build a collaborative review packet

For each candidate, present all variants and record:

- the concrete use and trigger each variant proposes;
- the evidence, repository situation, or speculation that motivated it;
- the approach and nuance preserved by that variant;
- every relationship to current top-level skills, always-loaded guidance, hooks, scripts, or neighboring variants;
- which text appears shared and which exception, authority scope, trigger path, causal reason, or operational boundary differs;
- unresolved questions, risks, and activation consequences;
- structural validation already run and any evidence still missing;
- available user-directed next actions without selecting one on the user's behalf.

Describe apparent redundancy as a falsifiable comparison. An existing skill may be incomplete, optional when the rule must be always loaded, trigger-unreachable for the affected task, authoritative at the wrong scope, or missing a counterexample or exception. Preserve those possibilities for review.

## Collaborate without collapsing history

- When the user asks for another approach, create another pending variant rather than replacing the earlier one.
- When the user asks to combine approaches, create a convergence variant that names every predecessor and explains what it adopts, changes, and leaves unresolved. Keep all predecessors intact.
- When the user requests or evidence requires a correction, determine whether it restores the declared design or changes it. Apply and commit a same-design correctness repair in the existing variant; create and commit a sibling for a design change. If the distinction is genuinely unresolved, surface that local decision while continuing independent review work rather than erasing either possibility.
- When the user says to retain, reject, or defer a candidate, report that decision without deleting the candidate. Removal is a distinct destructive effect requiring explicit authorization.
- Do not turn a favorable review into promotion. Review evidence helps the user decide; it does not establish an official skill architecture by itself.

## Separate promotion from enablement

Creating a nested pending variant is not promotion and is not enablement.

- **Pending creation:** write only beneath this package's `pending-review/` directory. Nested draft packages are not immediate children of the canonical skill repository and are not official discoverable skills.
- **Promotion as a new skill:** only after explicit user approval, copy the selected or converged draft into a new immediate-child canonical package. Retain the pending source unless separately authorized to remove it.
- **Merge into an existing skill:** only after explicit user approval naming the target and accepted variant. Recognize that editing a canonical package already exposed through harness symlinks can activate the change immediately.
- **Enablement:** installation, synchronization, linking, hook registration, configuration changes, and invocation policy are separate effects requiring explicit authority even after promotion.

Do not use lack of enablement authority as a reason to omit an explicitly requested pending artifact. Do not use creation authority as permission to promote or enable it.

## Validate without approving

Use `$skill-creator` to validate every complete nested draft package and any script it contains. Re-run `scripts/pending_skill_inventory.py` after adding variants or applying correctness repairs. Structural success and a candidate-root commit mean the artifact and its evolution are reviewable; they do not mean the candidate should be promoted or enabled.

Use subagents for forward evaluation only when the user separately authorizes delegation. Otherwise exercise written positive and negative scenarios locally and disclose that no independent forward evaluator ran.
