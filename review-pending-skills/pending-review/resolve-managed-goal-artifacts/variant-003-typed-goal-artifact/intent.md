# Intent: variant-003-typed-goal-artifact

## Concrete use

Resolve an exact harness-managed goal artifact from a structured goal objective without coupling harness state to skill package topology.

## Preserved approach

Carry managed objective artifacts as typed goal-response data and stop recovering them from prose.

Read a versioned managed_objective_artifacts list from the successful goal response, require exactly one supported file for the completion handoff, validate its containment and existence, and use objective prose only for human display.

## Difference from sibling variants

Keep this approach distinct from `variant-001-environment-root`, `variant-002-hook-context-root`, `variant-004-objective-path-validation`, `variant-005-installation-relative-root`. Do not converge implementation authority, activation effects, or failure semantics merely because common text could be shared.

## Causal evidence

The production hook derived codex_home from Path(__file__).resolve().parents[3]. Canonical execution through a synchronized symlink made that value ~, so the resolver searched ~/attachments and found zero candidates even though the objective contained one exact existing file under ~/.codex/attachments.

- `raw current-session tool event` at `completion-window.json: JSONL lines 2398-2400`: The successful update_goal response preserved the exact pasted objective path.
- `direct source inspection` at `~/agentic-skills/auto-skill-enhancer/scripts/goal_completion_hook.py:26-66,120,130`: The resolver accepts codex_home, but main derives it from the resolved script location.
- `durable reproduction` at `goal-file-resolution-diagnostic.json`: The hook-derived root returned null; observed CODEX_HOME returned the exact file.

## Validation planned

- zero, one, and multiple artifact records
- legacy objective-only response
- resume serialization
- pasted text and future non-text artifact kinds

## Uncertainty and risk

- Trusting arbitrary objective paths outside the managed attachments root.
- Treating custom CODEX_HOME as equivalent to a package location.
- Schema version skew between Codex and hook packages.
- Overfitting the current pasted-text wrapper wording.
- Retaining the installation-relative approach even though it is known to be fragile.

The candidate remains pending because structural validity does not decide whether this design should be promoted or merged into an existing owner.

## Questions for review

- Does this approach preserve the narrowest semantic owner?
- Is its authority source available in every intended harness and deployment topology?
- Should shared behavior remain a relationship or later converge into an existing skill?
- Which activation effects, if any, should the user separately authorize?

## Possible activation effects

- none during pending creation
- future promotion could alter automatic goal-completion handoff resolution
