---
name: audit-rollout-damage
description: "Build deterministic, non-applying damage assessments from agent or harness rollout JSONL, normalized tool-use evidence, and current artifact facts. Use when a user asks what unauthorized, tainted, mistaken, or superseded agent edits landed; wants qualitative and quantitative examples such as smallest, largest, mean-nearest, and median changes; needs inert remediation candidates distinguished from live effects; or wants aggressive, conservative, and recommended remediation options without applying them. Do not use this skill to infer user authority, apply reversals, modify protected goals, stage changes, or treat current source as proof that an edit was authorized."
---

# Audit Rollout Damage

Build a reproducible forensic report by separating trace extraction, evidence, adjudication, measurement, rendering, and remediation authority.

## Freeze effects and authority

- Treat the workflow as read-only except for explicitly requested forensic outputs beneath the selected scratch or report root.
- Do not restore, delete, rewrite, stage, unstage, commit, push, edit a living goal, or apply an inverse plan.
- Treat direct user instructions and protected authority as adjudication inputs. A rollout trace, current source, generated report, test, goal status paragraph, or mechanically exact inverse cannot create authority.
- Distinguish landed effects from inert remediation candidates. “Inert” means a candidate or report has not applied its proposed operation; it never means the landed change is harmless, disabled, verified, approved, or already reversed.

## Build normalized evidence

1. Resolve the exact rollout files, repository root, authority boundary, and output root from current user authority. Do not enumerate unrelated sessions merely because they are nearby.
2. Run `scripts/index_rollout_tools.py` for the explicitly selected rollout JSONL. The index preserves ordinals, call IDs, raw inputs, correlated outputs, session hashes, and home-normalized paths.
3. Run `scripts/discover_edit_candidates.py` against that index and the selected repository. Treat its results as candidates, not a complete or authoritative mutation inventory. Manually classify unsupported or ambiguous tool shapes rather than silently excluding them.
4. Create a small incident selection document and run `scripts/extract_rollout_context.py` for every edit or operation selected as a statistical representative. Select by stable ordinal or call ID and retain enough preceding and following semantic events to show the user request, assistant explanation, tool call, and result. The extractor records observable origin hints such as `direct_user_message` and `harness_internal_goal_context`; those hints are trace facts, not authority decisions.
5. Preserve additional normalized evidence—goal edits, test-ledger rows, index objects, file hashes, or non-patch effects—in separate JSON or JSONL artifacts. Never bury those observations in renderer source.

## Adjudicate through a manifest

Create one incident manifest conforming to `references/assessment-manifest.schema.json`.

- Put incident names, paths, ordinals, classifications, qualitative explanations, limits, and remediation options only in the manifest.
- Hash every evidence input and give each one a stable identifier. The renderer refuses a stale or missing input.
- Define each qualification level as remediation-confidence evidence, behavioral severity, or another explicit dimension. Never silently mix dimensions.
- Give each statistical record a generic measurement expression that selects and aggregates source evidence. Do not paste a precomputed size into renderer code.
- Cite every record and qualitative example to one or more evidence inputs and locators.
- Supply one `representative_assessments` dossier for every unique record selected as smallest, largest, mean-nearest, or median. A dossier must contain one or more machine-resolved `verbatim_exhibits` showing the exact before/after text, normalized patch lines, attempted patch, or prior artifact text needed to see the change itself. It must also explain the prior state, exact change, surrounding trace context, stated rationale, authority assessment, behavioral and causal effects, consequences of keeping and reversing it, recommended disposition, confidence, and unknowns. Every substantive statement carries an evidence citation.
- Treat measurement as selection only. Restating line counts, row counts, status labels, or file summaries in prose is not a qualitative assessment.
- Make each dossier sufficient for a remediation decision without requiring the reader to open source, reconstruct the conversation, or ask what the edit means. A selected excerpt from a large artifact must identify what is omitted and show the load-bearing public surface, authority transfer, behavior branch, or statement change on which the interpretation depends. If frozen evidence cannot supply verbatim text, say so as an explicit unknown and do not call the dossier decision-grade.
- Define one self-contained decision-evidence packet for every remediation boundary. The packet gives a complete semantic inventory of the changes covered and embeds an expandable, machine-resolved appendix containing every exact frozen patch or trace fragment in that boundary. Never ask the user to “review every hunk” without rendering those hunks and explaining their effects in the report itself.
- Define concrete remediation units for every option. Each unit names the affected artifacts or statements, links its decision-evidence packet, states exactly what the option retains, removes or restores, and leaves for a user decision, and says separately what `Approved` and `Reject` record. General instructions such as “restore the tracked targets” or “review mixed authority” are not decision-ready without that mapping.
- Render an editable `User Verdict` placeholder after the evidence link and the explicit `Approved`/`Reject` meanings, with the choices `Approved`, `Reject`, and `Question/Comment`, followed by a separate comment placeholder. A report is not review-ready when the user must invent where or how to record a decision or inspect source to discover what the verdict covers.
- Keep factual observations, protected authority, assistant interpretation, and user-selected remediation decisions distinguishable.

Read `references/qualification-model.md` before defining qualification levels or using “inert.”

## Render and reproduce

Run:

```bash
python3 scripts/render_damage_assessment.py \
  --manifest <assessment-manifest.json> \
  --output-markdown <detailed-damage-assessment.md> \
  --output-json <detailed-damage-assessment.json>
```

The renderer must compute counts, totals, means, medians, smallest/largest examples, the real record nearest the mean, and one or two real records bracketing the median. It renders incident prose from manifest data; it contains no incident-specific conclusions. When one record fills multiple roles, the report maps all roles to that record and renders its dossier once.

Then run:

```bash
python3 scripts/verify_damage_assessment.py \
  --manifest <assessment-manifest.json> \
  --output-root <absent-reproducibility-directory> \
  --output <reproducibility.json>
```

Require two fresh runs to produce byte-identical Markdown and JSON. Reproducibility proves deterministic rendering against frozen evidence; it does not prove semantic correctness, authority, or that a remediation should be applied.

## Review the generated report

Confirm that the generated report:

- explains the difference between live damage and inert remediation data with concrete examples;
- shows complete qualification inventories and computed representatives for every level;
- gives every computed representative a self-contained decision dossier rather than a quantitative caption;
- prints verbatim evidence for every dossier before interpreting it, labels attempted versus landed text, and discloses every omission from a selected excerpt;
- describes qualitative ownership, API, schema, workflow, test, goal, and artifact changes supported by the evidence, including the trace rationale and the authority that did or did not support it;
- renders a semantic inventory plus complete expandable exact-patch appendix for every remediation boundary, so no verdict depends on reopening source or session logs;
- provides aggressive, conservative, and recommended remediation options with named decision units, evidence-packet links, exact retain/remove-or-restore/undecided outcomes, explicit `Approved` and `Reject` meanings, reasons, risks, and authorization boundaries;
- gives every remediation decision unit an editable `User Verdict` and `User Question/Comment` review surface only after its decision evidence and verdict meanings;
- names unknowns and unsupported trace shapes rather than converting them into certainty;
- records the manifest and evidence hashes needed to reproduce the report.

Stop after the report and evidence are reviewable. Applying any remediation is a separate user-authorized phase.
