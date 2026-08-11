# Qualification and effect model

## Keep three dimensions separate

1. **Landed-effect state** answers whether an operation changed the current artifact, failed before landing, or remains uncertain.
2. **Remediation confidence** answers how exactly a possible future repair can be reconstructed: exact prior bytes, exact-hash new path, statement-level reconstruction, or unresolved evidence.
3. **Behavioral severity** answers how much product, authority, or workflow behavior the landed change may affect.

A small edit can have high severity. A one-line module export can activate thousands of lines. A deletion hunk can record zero changed body lines while removing a large tracked file. Report the measurement caveat beside every level.

## Use “inert” narrowly

An inert remediation candidate is data that describes a possible operation and its preconditions without performing it. It may contain an exact prior object identifier, a current SHA-256 guard, a statement-level patch, or a manual-review marker.

“Inert” does not mean that the landed repository change is inert. It also does not mean harmless, approved, verified, executable, selected, reversible without review, or authorized for application.

## Select statistical examples deterministically

Within one level and one metric unit:

- sort records by computed size, then identity, then record ID;
- report the first stable record among equal-size smallest or largest ties and disclose the tie count;
- calculate arithmetic mean from every record and select the real record or tied records with minimum absolute distance from it;
- calculate the numeric median; for an odd record count show the middle record, and for an even count show both bracketing records;
- retain the complete record inventory so examples cannot hide omitted units.

These examples describe the metric distribution. They are not a severity ranking or remediation decision.

## Require qualitative decision dossiers

Statistics select representative records; they do not explain them. For every unique record selected as smallest, largest, mean-nearest, or median, write one cited dossier that lets a reader decide what to do without opening source or reconstructing the rollout.

The dossier must answer:

- What exact text changed? Show the frozen before/after text or normalized patch lines verbatim rather than describing their size.
- What state existed before the operation?
- What changed, including the behavior or authority it added, removed, or redirected?
- What direct user message, assistant explanation, tool call, and result surround the change?
- What rationale did the assistant state, and did the available user authority support that rationale?
- Which upstream and downstream artifacts depend on the change?
- What happens if the change is kept? What happens if it is reversed?
- What disposition is recommended, why, what risk remains, how confident is the assessment, and what is still unknown?

A file summary with a line, row, byte, or operation count is quantitative even when written as prose. A status label such as `landed_mixed_statements` is classification metadata, not a qualitative explanation. If one record fills several statistical roles, list every role but render the dossier once.

## Require verbatim exhibits

Resolve exhibit bodies from hash-verified evidence at render time. Do not paste incident text into renderer source or accept an uncited manually typed quotation as evidence.

- Use a complete normalized patch when it is short enough to show the whole change.
- For a failed call, show the exact attempted patch and label it `attempted_not_landed`.
- For a deletion whose normalized hunk lacks body lines, show the exact delete operation and a prior-state excerpt from frozen trace evidence.
- For a large added or changed artifact, show the load-bearing type, public function, behavior branch, or authority statement and list the omitted regions explicitly.
- For mixed statement artifacts, show every changed statement needed to distinguish the valid and invalid subsets.
- Treat an exhibit as selected evidence, not a claim that omitted code is unimportant. The prose interpretation must stay within what the shown text and cited evidence support.

## Make remediation options concrete

First define one decision-evidence packet for each remediation boundary. The packet must contain:

- a complete semantic inventory of every behavior, authority, API, schema, test, goal, or artifact change covered by the boundary;
- the exact artifacts or statements associated with each semantic change;
- why each change matters to the remediation decision;
- an expandable, machine-resolved appendix containing every exact frozen patch or trace fragment covered by the boundary.

Then, for aggressive, conservative, and recommended options, define named decision units. Each unit must list:

- the exact artifacts, paths, statements, or rows in scope;
- its decision-evidence packet;
- what the option retains;
- what it removes or restores;
- what still requires a user decision;
- what recording `Approved` selects for a later separately authorized remediation phase;
- what recording `Reject` rules out without silently selecting another option;
- an editable `User Verdict` placeholder offering `Approved`, `Reject`, or `Question/Comment`, plus a separate comment field;
- why that boundary follows from the evidence.

A reader must be able to compare the three options and enter a verdict without translating counts such as “17 tracked targets” back into source paths, reopening the rollout, inspecting product source, or asking what the hidden hunks do.
