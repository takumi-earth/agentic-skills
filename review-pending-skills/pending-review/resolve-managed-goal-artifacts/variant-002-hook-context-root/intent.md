# Intent: variant-002-hook-context-root

## Concrete use

Resolve an exact harness-managed goal artifact from a structured goal objective without coupling harness state to skill package topology.

## Preserved approach

Add a typed codex_home or attachments_root field to PostToolUse and prefer that event value over process environment.

Consume a versioned hook-context root supplied by Codex, validate it as the managed harness root, retain CODEX_HOME and ~/.codex only as backwards-compatible fallbacks, and report which authority source selected the root.

## Difference from sibling variants

Keep this approach distinct from `variant-001-environment-root`, `variant-003-typed-goal-artifact`, `variant-004-objective-path-validation`, `variant-005-installation-relative-root`. Do not converge implementation authority, activation effects, or failure semantics merely because common text could be shared.

## Causal evidence

The production hook derived codex_home from Path(__file__).resolve().parents[3]. Canonical execution through a synchronized symlink made that value ~, so the resolver searched ~/attachments and found zero candidates even though the objective contained one exact existing file under ~/.codex/attachments.

- `raw current-session tool event` at `completion-window.json: JSONL lines 2398-2400`: The successful update_goal response preserved the exact pasted objective path.
- `direct source inspection` at `~/agentic-skills/auto-skill-enhancer/scripts/goal_completion_hook.py:26-66,120,130`: The resolver accepts codex_home, but main derives it from the resolved script location.
- `durable reproduction` at `goal-file-resolution-diagnostic.json`: The hook-derived root returned null; observed CODEX_HOME returned the exact file.

## Validation planned

- typed field preferred over conflicting environment
- old event schema environment fallback
- missing all authority sources
- cross-platform path serialization

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
