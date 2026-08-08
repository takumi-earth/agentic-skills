---
name: implement-strict-work
description: "Implement owner-first, capability-preserving changes in the `strict*` ecosystem. Use for feature work, refactors, migrations, compile or Clippy remediation, mutation survivors, coverage gaps, duplicate code, dead code, generated-code lint, parser or macro changes, fixtures, and multi-repository convergence. This skill forbids diagnostic-driven local carve-outs and does not grant verification or commit authority."
---

# Implement Strict Work

Change the owner of the behavior, preserve the intended capability, and converge all authorized consumers to the complete end state.

## Reconfirm authority and target state

Before editing:

- Re-read the current task contract and approved plan.
- Use `$maintain-living-goal` to reconcile the complete owner-level slice before source edits and to prune only after that slice is complete.
- Use `$protect-causal-architecture` when current source, a refactor, or a proposed simplification changes a protected owner, phase edge, barrier, failure order, cleanup, or persistence rule.
- When the user designates a goal or plan file as a living implementation contract, update the affected decision in place with each authorized correctness change. Rewrite or remove contradicted instructions instead of appending progress notes; the file records authority already granted and does not create new authority.
- Keep that living contract causal, not merely factual. Preserve why each load-bearing owner, invariant, ordering, capability split, boundary, or verification distinction must remain true and what deviation it prevents; prune superseded chronology, not architectural rationale.
- Confirm owned writes, forbidden paths, method constraints, and current phase.
- Confirm settled ownership, API, compatibility, and distribution decisions.
- Separate implementation commands from verification commands.
- Treat a dirty worktree as a merge-safety condition only.

Do not implement if load-bearing ownership, public API, compatibility, or end-state choices remain unresolved. Surface the missing choice rather than deciding it silently.

Work one complete slice at a time: investigate the full owner boundary, reconcile the goal, implement every required behavior and polarity, close the authorized diagnostic batch, format, repeat affected symbol scans after formatting, prune to current fact, then investigate the next slice. If this loop repeats without closing a slice or producing a new owner-level decision, mark the goal blocked.

## Trace every symptom upstream

For a compile error, lint, mutant, coverage gap, duplicate, generated failure, or fixture problem:

1. Describe the behavior the diagnostic exposes.
2. Identify the generator, macro expansion, parser/IR model, type invariant, API boundary, feature split, module topology, workflow, protocol, or harness that owns the shape.
3. Distinguish truly obsolete code from intended but incomplete wiring.
4. Refactor the owner.
5. Add positive and negative behavior evidence at that boundary.
6. Remove local debt and converge affected consumers.

The diagnostic is acceptance evidence, not architecture.

## Reject local carve-outs

Do not rationalize:

- `#[allow]` or `#[expect]`;
- lint, coverage, mutation, duplication, snapshot, or generated-source policy changes;
- static exclusions or deviation tables;
- direct generated-output edits;
- `#[path]` or `include!`-based module routing used as an ownership or visibility workaround; use the natural module hierarchy instead;
- compatibility shims, token aliases, re-exports, or broadened public API;
- filler calls, filler tests, defensive unreachable branches, or underscored discards;
- test-only, generated, pre-existing, stage-local, or non-gating exceptions;
- non-idiomatic checked-in fixtures when parser data, tokens, IR, snapshots, or temporary crates test the contract more narrowly.

Use a narrow exception only when the current repository contract or the user explicitly authorizes the exact lint or site category with semantic criteria. Apply it only at qualifying sites, include every required contextual justification, and do not infer adjacent exemptions.

## Preserve behavior while changing structure

- Inventory public and internal capabilities before extraction, upgrade, or simplification.
- Treat strict-owned forks and local product crates as refactoring surfaces, not immutable external limitations.
- Do not reduce lifecycle, schema, protocol, output, error, macro, or test-support behavior merely to align with upstream or make a new abstraction compile.
- Decode, validate, and report errors at typed boundaries; do not convert unsupported or invalid input into quiet no-ops.
- Before deletion, prove semantic obsolescence and identify the owner of any incomplete wiring.
- Do not call a test stale because partial implementation no longer expresses its scenario. Use `$verify-test-parity` whenever tests are deleted, moved, renamed, consolidated, or broadly rewritten, and require evidence of intentional production-capability retirement for every obsolete test.
- Before creating a helper, search for the existing ecosystem abstraction and extend its owner when appropriate.
- Name abstractions after capabilities and invariants, not current callers or workflows.

Do not turn naming cleanup into the implementation objective. Rename only when the corrected capability would otherwise remain materially misleading.

Public API additions, removals, re-exports, compatibility surfaces, and ownership transfers require explicit resolution when the plan did not already settle them.

## Converge generated and multi-repository surfaces

- Edit the fragment, generator, schema, template, or workflow owner.
- Run the owning generation path only when generation is authorized.
- Accept and report normal generated fallout; do not hand-copy or imitate missing tooling.
- Build a consumer matrix for cross-repository changes.
- Land replacement capability with removal of the old path.
- Do not leave known broken consumers for a later cleanup pass unless the user explicitly stages the end state that way.
- Do not make a consumer-specific implementation the shared policy owner.

## Protect concurrent work

- Read and integrate current contents of touched files.
- Treat current files and live callers as correctness authority unless the user explicitly names a diff or historical revision as the task target. Use Git state otherwise only for preservation or provenance; never let it shrink implementation scope.
- Ignore unrelated dirty files.
- Do not attribute changes to yourself without causal evidence.
- Never restore, reset, checkout, clean, stage, unstage, or overwrite unexpected changes.
- Run the repository's real formatting command when implementation authorizes formatting; do not substitute a check-only form because the tree is dirty.
- Report unrelated artifact fallout from canonical workflows plainly.

## Finish at the requested boundary

Complete all in-scope edits and behavior tests. Then report separately:

- implementation state;
- generated or cross-repository convergence state;
- authorized diagnostics run;
- canonical acceptance gate state;
- remaining external blocker or user-owned decision.

Do not claim verification or acceptance from code inspection, focused diagnostics, worker reports, or an unrun top-level gate.
