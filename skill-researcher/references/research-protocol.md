# Trace research protocol

## Contents

1. Evidence hierarchy
2. Classification taxonomy
3. False-positive controls
4. Sampling and saturation
5. Delegated report contract
6. Cross-partition synthesis
7. Skill-portfolio design
8. Research limitations

## Evidence hierarchy

Use evidence in this order:

1. Live user instruction or correction in its chronological context.
2. Tool call and tool output proving the assistant's concrete action.
3. Assistant acknowledgement corroborated by nearby trace evidence.
4. Repository or configuration evidence inspected during the session.
5. Assistant, worker, or compaction summary used only when independently corroborated.

Do not establish a behavioral finding from a final answer, keyword count, model reasoning record, or summary alone.

For every material episode, retain:

- harness;
- family and session identifiers;
- recorded CWD;
- absolute JSONL path;
- exact source line or compact line range;
- timestamp when available;
- controlling instruction;
- observed action or response;
- classification;
- recurrence, severity, and churn assessment;
- counterexample or uncertainty where relevant.

Keep quotations short. Let the citation and paraphrased context carry the finding.

## Classification taxonomy

Use one primary classification per episode:

- `initial-constraint`: A rule given before action. Use as trigger evidence or as the controlling contract, not as proof of a previous violation.
- `clarification`: The user makes an ambiguous request concrete. Do not assume the earlier behavior was wrong unless the prior context establishes that.
- `confirmed-violation`: Tool evidence or a concrete acknowledgement proves an already-stated boundary was crossed.
- `architecture-or-judgment-correction`: The assistant chose the wrong owner, abstraction, invariant, policy, or factual premise.
- `avoidable-churn`: Rework was materially caused by a preventable instruction, ownership, planning, or verification mistake.
- `external-or-tooling-churn`: Authentication, API, permission, session, network, tool, or harness failure not caused by the skill opportunity under study.
- `evolving-requirement`: The user legitimately changed or added a requirement after earlier work. Do not rewrite chronology into a prior violation.
- `user-self-correction`: The user corrected their own wording or fact. Exclude from assistant-failure counts.
- `positive-control`: Comparable work followed the desired protocol without correction.
- `unresolved`: Evidence is insufficient or contradictory.

Separate classification from severity. A clarification can reveal a valuable trigger even when it is not a violation; a confirmed violation can still be isolated and unsuitable for a permanent skill.

## False-positive controls

Exclude or label distinctly:

- injected `AGENTS.md`, `CLAUDE.md`, system, developer, environment, and skill text;
- compaction and carried-forward summaries;
- quoted prior dialogue and pasted examples;
- worker assignment packets echoed as `user` messages;
- teammate reports, idle notices, shutdown notices, and task notifications;
- duplicate user turns copied into full-history forks;
- negative imperatives in an initial request;
- tool output containing correction vocabulary;
- assistant-generated proposed wording later pasted by the user;
- user self-corrections;
- factual disagreements not followed by an action;
- ordinary discovery questions;
- external failures and command fallout;
- genuinely evolving requirements.

Do not equate a high correction-signal count with a high number of failures. Reconstruct the primary chronology and family lineage first.

Use positive controls to test whether a proposed rule distinguishes failure from successful execution. If it condemns the clean control, narrow or discard it.

## Sampling and saturation

Construct a purposive sample rather than reading only the highest signal counts:

- include at least the largest families by bytes or user turns;
- include the strongest correction/churn leads;
- include recent low-signal controls;
- include different task modes and repositories;
- inspect a primary session with representative workers when orchestration matters;
- include each harness needed for the claim.

Track the number of families, source files, primary/subagent traces, user turns, bytes, and heuristic hits inspected.

Reach saturation only after later controls and additional high-signal families add no new actionable top-level class. State what later samples repeated and what remained unsampled.

Do not use saturation language to imply statistical prevalence. Report qualitative recurrence and evidence diversity.

## Delegated report contract

When delegation is explicitly authorized, give each worker:

- its harness and disjoint partition manifest;
- a unique owned report path;
- the research question and shared classification taxonomy;
- explicit read-only scope;
- prohibited edits and prohibited sibling work;
- required large/high-signal/recent/control sampling;
- family-level deduplication rules;
- exact false-positive exclusions;
- evidence fields and citation format;
- saturation stop condition;
- the sole allowed validation, normally confirming that its report exists and is non-empty;
- a final handoff containing sample counts, ranked findings, controls, candidate skills, limitations, and report path.

Do not leak the expected finding or desired skill split into the packet. Ask workers to seek disconfirming evidence and report no finding where appropriate.

Do not let workers create skills, edit shared synthesis, modify inventories, or decide the final portfolio. Keep those responsibilities with the root researcher.

## Cross-partition synthesis

Normalize worker labels into stable concepts only after reading their cited evidence. Merge findings that share:

- the same trigger;
- the same semantic owner;
- the same corrective mechanism;
- compatible degrees of freedom.

Keep findings separate when their triggers or control surfaces differ even if they share a broad theme. For example, staged-only commit mechanics and general task authority can reinforce each other while remaining separate skills because one is near-zero freedom and one is an always-on foundation.

Require cross-harness evidence for cross-harness claims. Otherwise label the result harness-specific.

Record:

- recurrence across independent families, not copied forks;
- recurrence across repositories and task modes;
- severity and avoidable churn;
- clean controls;
- contradictory cases;
- evidence gaps;
- whether current explicit instructions supersede older history.

## Skill-portfolio design

Map stable findings to skills by trigger and responsibility:

- Put universal, compact invariants in a small foundation.
- Put low-freedom mechanical workflows in narrow task skills.
- Put domain-specific details in references loaded only for that task.
- Add scripts only for repeated deterministic extraction or validation.
- Keep frontmatter descriptions precise enough to trigger without loading unrelated bodies.
- Avoid overlapping skills that can issue inconsistent instructions for the same phase.
- Prefer strengthening the semantic owner over duplicating the same rule in every consumer skill.

For every candidate, specify:

- proposed name;
- trigger description;
- semantic owner;
- degree of freedom;
- evidence-backed contract;
- exclusions and non-triggers;
- existing-skill overlap;
- forward-test scenarios;
- expected context cost.

Research recommendations do not authorize package creation. Hand approved candidates to `$skill-creator`.

## Research limitations

State at least:

- snapshot date and corpus roots;
- malformed records and skipped content;
- heuristic selection bias;
- family-linkage uncertainty;
- sampling coverage;
- harness schema drift risk;
- historical-preference drift;
- whether the study is qualitative or quantitative;
- whether current source state was re-adjudicated;
- whether source traces continued growing after inventory.
