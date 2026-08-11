---
name: audit-rollout-damage
description: "Build deterministic, non-applying damage and reasoning-failure assessments from agent or harness rollout JSONL, normalized tool-use evidence, and current artifact facts. Use when a user asks what unauthorized, tainted, mistaken, brittle, or superseded agent edits landed; why an agent adopted a shortcut despite explicit architecture; when parser or AST façades, copied precedent, circular tests, or unexecuted evidence may have hidden the failure; when quantitative representatives are needed; or when remediation options must remain inert. Do not use this skill to infer user authority, apply reversals, modify protected goals, stage changes, or treat current source as proof that an edit was authorized."
---

# Audit Rollout Damage

Build a reproducible forensic report by separating trace extraction, evidence, adjudication, measurement, rendering, and remediation authority.

## Freeze effects and authority

- Treat the workflow as read-only except for explicitly requested forensic outputs beneath the selected scratch or report root.
- Do not restore, delete, rewrite, stage, unstage, commit, push, edit a living goal, or apply an inverse plan.
- Treat direct user instructions and protected authority as adjudication inputs. A rollout trace, current source, generated report, test, goal status paragraph, or mechanically exact inverse cannot create authority.
- Distinguish landed effects from inert remediation candidates. “Inert” means a candidate or report has not applied its proposed operation; it never means the landed change is harmless, disabled, verified, approved, or already reversed.

## Build normalized evidence

Artifact persistence and helper execution require current authority separate from review authority. For a read-only inline review, inspect the exact selected rollout and current source in place, return the causal verdict inline, and do not create `.scratchpad/` artifacts or run output-producing helpers. When a deterministic persisted assessment is explicitly requested or otherwise authorized:

1. Resolve the exact rollout files, repository root, authority boundary, and output root from current user authority. Do not enumerate unrelated sessions merely because they are nearby.
2. Run `scripts/index_rollout_tools.py` for the explicitly selected rollout JSONL. The index preserves ordinals, call IDs, raw inputs, correlated outputs, and session hashes while recursively normalizing expanded current-home paths in serialized inputs and outputs.
3. Run `scripts/discover_edit_candidates.py` against that index and the selected repository. It recognizes direct calls and strict JSON-object `tools.exec_command(...)` calls nested inside an outer `exec` JavaScript wrapper. It records mutation-shaped wrappers it cannot parse as unsupported evidence, and reports success or failure only from explicit structured exit or result semantics; absent or contradictory semantics remain unknown. Treat all results as candidates, not a complete or authoritative mutation inventory. Manually classify unsupported or ambiguous tool shapes rather than silently excluding them.
4. Create a small incident selection document and run `scripts/extract_rollout_context.py` for every edit or operation selected as a statistical representative. Select by stable ordinal or call ID and retain enough preceding and following semantic events to show the user request, assistant explanation, tool call, and result. The extractor records observable origin hints such as `direct_user_message` and `harness_internal_goal_context`; those hints are trace facts, not authority decisions.
5. Preserve additional normalized evidence—goal edits, test-ledger rows, index objects, file hashes, or non-patch effects—in separate JSON or JSONL artifacts. Never bury those observations in renderer source.

## Reconstruct reasoning failure causally

When the user asks why the agent chose a brittle or prohibited mechanism, reconstruct the decision sequence from the trace rather than relying on a later apology or current source shape.

1. Locate the earliest user-selected or protected architecture statement.
2. Record separately what the agent read or accurately restated and what its plan, helper API, first artifact, and landed implementation actually did. Restatement proves awareness, not compliance; a later apology or diagnosis is corroboration, not the causal source of truth.
3. Locate the first nearby precedent, helper API, plan wording, or convenience pressure that the agent treated as implementation authority.
4. Locate the first concrete artifact that locks in the shortcut, not merely the largest later example.
5. Track the reinforcing signal: passing circular tests, copied fixtures, checklists closed from test-source presence, or implementation status rewritten as architecture.
6. Name the primary abstraction failure separately from enabling precedent, API incentives, reinforcing evidence, visibility or accounting failures, and later accelerants.
7. Separate later pressure, batching, compaction, or verification deferral from the original cause by comparing timestamps and ordinals. Do not name one as root cause when the defective abstraction predates it.
8. Use contemporaneous rollout calls, outputs, and captured after-state to establish historical actions and lock-in. Treat current source only as evidence of the current residual state; later source cannot prove what existed, landed, or was understood at an earlier ordinal. Compare that residual state with the protected invariant to determine whether cleanup removed only visible tests or also repaired the production mechanism.

Classify category substitutions explicitly, including:

- **parser or AST façade:** writes are syntax-bounded, but discovery or eligibility still depends on fixed paths, rendered fragments, complete token snapshots, or exact spellings;
- **snapshot laundering:** a full source body becomes a normalized token list, fingerprint, hash, regex, or other equivalent exact representation;
- **semantic-label laundering:** a diagnostic string or field name implies semantic ownership without resolution or workspace discovery;
- **test-oracle laundering:** parsed syntax is rendered back to text and asserted through substrings, equality, regexes, or snapshots;
- **legacy-precedent laundering:** a nearby brittle helper is copied despite a higher-authority semantic requirement;
- **circular green evidence:** the implementation emits the same strings the test searches for without proving which owner or node changed;
- **unexecuted-evidence closure:** the presence of test source or ledger text is reported as behavioral proof after execution was deferred or failed.

Test the claimed oracle counterfactually. Ask whether the same test could pass if an equal-looking node in the wrong owner changed, if the target moved files, or if unrelated syntax changed. Record a concrete false-positive construction when possible.

Count defective tests and mechanisms by semantic oracle class, not only by obvious method names. Include wrapper helpers, exact equality, snapshots, parse-then-text conversions, and copied bodies so a second search style cannot hide residual cases.

Use `$design-semantic-source-transforms` to describe the durable production replacement and `$test-adaptive-source-transforms` to describe equal-or-stronger evidence. When the current production mechanism or every caller needs a checkpointed, source-complete disposition packet, hand that source-adjudication slice to `$audit-architectural-regressions`; keep rollout ordinals and trace evidence authoritative for causal history. Keep every replacement as remediation analysis unless the user separately authorizes implementation.

## Adjudicate an authorized persisted assessment

When persistence is authorized, create one incident manifest conforming to `references/assessment-manifest.schema.json`.

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

## Render and reproduce an authorized assessment

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

For an inline read-only review, report the same authority distinctions, causal ranking, representative evidence, current residual state, unknowns, and remediation boundaries directly. State that no persisted report, generated evidence, or executable probe was created.

Stop after the report and evidence are reviewable. Applying any remediation is a separate user-authorized phase.
