# Intent: variant-002-hook-context-root

## Concrete use

Consume the paired `codex-runtime-context/v1` specification under explicit profile selection. Use a valid bound event root for managed references and preserve the independent exact-user-path operation.

## Preserved approach

Consume the paired versioned `runtime_context.codex_home` profile and prefer its valid bound root over process environment.

Use the explicit event/legacy profile contract, trusted namespace/home binding, and absent/invalid distinction. Keep exact user-designated paths independent from managed-root resolution.

## Difference from sibling variants

Keep this approach distinct from `variant-001-environment-root`, `variant-003-typed-goal-artifact`, `variant-004-objective-path-validation`, `variant-005-installation-relative-root`. Do not converge implementation authority, activation effects, or failure semantics merely because common text could be shared.

## Causal evidence

The following records describe the original failure. Current owner locations and protocol limits are attributed separately in the corrected references.

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

- Confusing an unselected path in prose with a current explicit user designation.
- Treating custom CODEX_HOME as equivalent to a package location.
- Schema version skew between Codex and hook packages.
- Overfitting the current pasted-text wrapper wording.
- Retaining the installation-relative approach even though it is known to be fragile.

The approved specification corrections are complete. Retention now concerns adoption of this inert alternative, not deferred repairs. Implementation and enablement require a selected producer and separate authority.

## Questions for review

- Does this approach preserve the narrowest semantic owner?
- Is its authority source available in every intended harness and deployment topology?
- Should shared behavior remain a relationship or later converge into an existing skill?
- Which activation effects, if any, should the user separately authorize?

## Possible activation effects

- none during pending creation
- future promotion could alter automatic goal-completion handoff resolution
