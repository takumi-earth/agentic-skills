---
name: implement-strict-work
description: "Implement owner-first, capability-preserving changes in the `strict*` ecosystem. Use for feature work, refactors, migrations, compile or Clippy remediation, mutation survivors, coverage gaps, duplicate code, dead code, generated-code lint, parser or macro changes, fixtures, and multi-repository convergence. This skill forbids diagnostic-driven local carve-outs and does not grant verification or commit authority."
---

# Implement Strict Work

Change the owner of the behavior, preserve the intended capability, and converge all authorized consumers to the complete end state.

## Reconfirm authority and target state

Use the current task contract. Do not repeat intake, rebuild an audit, or reconcile a living goal before every edit when authority and target architecture are unchanged.

Before editing a new owner-level slice:

- Re-read the current task contract only if context, scope, or authority changed.
- Use `$maintain-living-goal` when a user-designated living goal actually needs an in-place requirement or status update; do not make goal reconciliation a source-edit prerequisite.
- Use `$protect-causal-architecture` only when the change would alter a user-protected or genuinely disputed owner, phase edge, barrier, failure order, cleanup, or persistence rule.
- When the user designates a goal or plan file as a living implementation contract, update the affected decision in place with each authorized correctness change. Rewrite or remove contradicted instructions instead of appending progress notes; the file records authority already granted and does not create new authority.
- Keep that living contract causal, not merely factual. Preserve why each load-bearing owner, invariant, ordering, capability split, boundary, or verification distinction must remain true and what deviation it prevents; prune superseded chronology, not architectural rationale.
- Confirm owned writes, forbidden paths, method constraints, and current phase.
- Confirm settled ownership, API, compatibility, and distribution decisions.
- Separate implementation commands from verification commands.
- Treat a dirty worktree as a merge-safety condition only.

Do not implement the work that depends on unresolved load-bearing ownership, public API, compatibility, or end-state choices. Surface the missing choice rather than deciding it silently, and continue every authorized owner-level slice that is causally independent of it.

Work one complete vertical slice at a time: identify the owner and intended behavior, implement the structural change, add the required positive and negative evidence, format when authorized, and continue. Update a living goal only when its authoritative requirements or material status changed. If repeated attempts expose a real unresolved owner-level decision, stop that dependent slice and continue any independent authorized work.

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

Treat checked-in compile-diagnostic Rust source as justified only when full `rustc` integration is itself the behavior under test. Even in that narrow case, normalize or delete incidental non-idiomatic syntax that is not required to produce the diagnostic; a compile-fail label is not an exemption from the repository's structural constraints.

Use a narrow exception only when the current repository contract or the user explicitly authorizes the exact lint or site category with semantic criteria. Apply it only at qualifying sites, include every required contextual justification, and do not infer adjacent exemptions.

## Preserve behavior while changing structure

- Identify affected public and internal capabilities while migrating the owner; do not require a repository-wide inventory unless the user requested one or the change cannot otherwise be bounded safely.
- Treat strict-owned forks and local product crates as refactoring surfaces, not immutable external limitations.
- Do not reduce lifecycle, schema, protocol, output, error, macro, or test-support behavior merely to align with upstream or make a new abstraction compile.
- Decode, validate, and report errors at typed boundaries; do not convert unsupported or invalid input into quiet no-ops.
- Before deletion, prove semantic obsolescence and identify the owner of any incomplete wiring.
- Do not call a test stale because partial implementation no longer expresses its scenario. Map touched tests to equal-or-stronger owner-level evidence as they are rewritten. Use `$verify-test-parity` only when the user explicitly requests a comprehensive parity audit; if local mappings expose an unresolved live contract, report it and ask before starting that audit.
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
- Treat current files and live callers as authority for factual current state unless the user explicitly names a diff or historical revision as the task target. They do not silently supersede user-selected protected target architecture. Use Git state otherwise only for preservation or provenance; never let it shrink implementation scope.
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
