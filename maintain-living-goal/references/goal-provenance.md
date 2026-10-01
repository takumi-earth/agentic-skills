# Goal provenance and protected edits

A goal edit records authority or evidence that already exists; it never creates authority for later implementation merely because the assistant wrote it into the goal.

Before each edit, classify every changed statement and retain its primary provenance:

- **Explicit user selection:** cite the user message or already protected packet that selected it.
- **Carried protected contract:** preserve its existing authority, causal edges, counterfactual, and evidence without changing their meaning.
- **Source-derived mutable fact:** cite the direct source, command, or external-authority observation and keep it factual; it may describe implementation status but may not add a target decision.
- **Assistant proposal:** keep it visibly proposed and non-authoritative. If it changes architecture, tests, a baseline, or an allowed mutator, route it through `$protect-causal-architecture` and wait for explicit user selection before dependent effects.

Never label an assistant-derived design “decision-complete,” rewrite it as implementation fact, or use it as the premise for source/test edits unless its authority can be traced past assistant-authored goal text to an explicit user decision or protected/source-derived contract. The goal itself is not independent corroboration for a statement the assistant inserted.

Keep decision, application, and verification as separate facts. A user's selection remains settled until an attributable user instruction explicitly supersedes that decision. New guard evidence, changed target bytes, Git representation changes, or stale prose may affect whether an effect can be applied or verified; they do not reopen the selection. When an application guard fails, report the mismatch and stop the dependent effect without manufacturing reassessment or renewed approval of the unchanged decision.

Mutable status cannot:

- change a parity or historical baseline;
- retire a production capability or protecting test;
- turn a removed architecture into a replacement-test obligation;
- add an authority read, mutator, barrier, compatibility surface, or migration;
- reinterpret implementation drift as the selected target.

When a status update would do any of those things, stop the dependent edit. Record the current packet, proposed packet, primary authority, affected tests, and counterfactual for user review. Do not implement the proposal first and then reconcile the goal to legitimize it.

When the user corrects a baseline, architecture, or test disposition, treat every downstream assistant-authored goal statement and dependent source/test edit as untrusted until a provenance audit revalidates or retracts it. Apply the correction across the whole goal in the same pass; a local wording fix that leaves a contradictory status claim is not a completed correction.

For the concrete failure that established these rules, load [the autonomous goal-edit regression](autonomous-goal-edit-regression.md) when auditing goal provenance, parity-baseline drift, or a correction that may have left dependent statements alive.
