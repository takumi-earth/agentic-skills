---
name: verify-test-parity
description: Close every removed-test disposition against a Git baseline and preserve equal-or-stronger behavioral coverage. Use when tests were deleted, renamed, moved, consolidated, or broadly rewritten; when brittle source-string, snapshot, copied-body, or marker tests are being replaced; when a large diff may have lost assertions; or when Codex must prove that every removed Rust `#[test]` has a behavioral replacement unless a production capability was intentionally removed and made the test obsolete.
---

# Verify Test Parity

Build and close a test-by-test behavioral ledger. Treat inventory counts and renamed functions as discovery evidence, never as proof of parity. Accept no unexplained removed test.

## Fix the baseline before auditing

Treat the Git baseline as user-selected authority, not as a value to rediscover from the evolving repository. Resolve a selected symbolic ref once to an immutable commit OID, record both the user's spelling and that OID in the task's durable audit state, and pass the same OID to every inventory and ledger command.

Never replace that baseline with `HEAD`, a later `HEAD^`, a newer checkpoint, the merge base, or the current worktree to reduce the removed-test inventory. If the selected baseline is missing or appears wrong, stop for user review; do not silently shrink or rebase the audit.

## Inventory the change

Run the comparator from the repository root:

```bash
parity_baseline_oid='<recorded immutable baseline OID>'
"$CODEX_HOME/skills/verify-test-parity/scripts/compare-test-inventory.sh" --baseline "$parity_baseline_oid" --repo .
```

When `CODEX_HOME` is unset, use the discovered skill path directly. Use `scripts/list-test-identities.sh` when a normalized baseline or worktree inventory is needed independently.

Interpret the comparator categories as follows:

- `removed`: a baseline path/name identity is absent from that path in the worktree.
- `moved-candidate`: the removed name exists under another worktree path; inspect both bodies because a matching name does not prove a faithful move.
- `globally-missing`: the old name exists nowhere in the worktree; locate a semantic replacement or identify an intentionally retired product behavior.
- `added`: a worktree path/name identity was absent from the baseline; it may be a replacement, a split polarity, or unrelated new coverage.

The scripts lexically discover Rust functions carrying `#[test]` or a namespaced `...::test` attribute. Supplement them with `git diff --name-status "$parity_baseline_oid"` and targeted diff inspection for deleted test files, doctests, macro-generated cases, snapshots, diagnostic fixtures, and non-Rust suites.

## Create the closure ledger

Maintain a tab-separated ledger with this exact header:

```text
baseline-path	test-name	disposition	replacement-path	replacement-test	production-capability-removal	evidence
```

Use one or more rows per removed baseline identity, with one row per independently observable old contract. A row closes a contract, not a test name and not an implementation mechanism:

- Use `replaced` only when the old observable contract remains live. Name one existing equal-or-stronger replacement per row, set `production-capability-removal` to `-`, and map the old input, output, failure, and effect assertions to that replacement. A test of the new architecture is not a replacement for deliberately retired old mechanics merely because both concern the same domain.
- Use `intentionally-retired` only for a contract whose owning production command, API, format, workflow, or effect was explicitly removed. Set both replacement fields to `-`, name that exact removed capability, and cite production-source or approved architecture evidence. A refactor or replacement architecture is not itself retirement evidence.

Split every aggregate baseline test into its independently observable contracts before choosing dispositions. The same old test may require both row kinds when live behavior moved to a new owner while a distinct mechanism was removed. Do not retire the whole test because one assertion became obsolete, and do not claim the whole test as replaced because one generic invariant survived.

Never invent a substitute test merely to make the ledger validate. Add a test only when a still-live contract lacks equal-or-stronger coverage. If the only uncovered assertion exercised an explicitly removed capability, retire that contract with evidence instead of recreating it under a new name.

Do not use retirement for a refactor, rename, changed implementation strategy, currently failing behavior, or difficult fixture. Those still require replacement coverage. Treat a passing ledger script as structural validation only; it cannot prove that a claimed replacement is semantically equivalent.

## Require behavioral replacement evidence

Judge replacement strength by the observed contract and owner, not by assertion count, fixture size, or similarity of expected text.

This skill owns the immutable baseline, contract decomposition, disposition ledger, and closure decision. `$test-adaptive-source-transforms` owns the structural oracle and adaptive replacement design. For a broad parsed-source rewrite, load both once: fix the parity baseline and ledger before deletion, design the replacement evidence, then close each ledger row from executed owner-level evidence.

A replacement does not close a live structural contract when it proves only that:

- a rendered substring, prefix, suffix, regular expression, snapshot, or complete source expectation appears;
- an upstream production body was copied into a fixture or expected value;
- source was parsed and the selected node was converted back to text before assertion;
- a marker function or comment whose name claims a product behavior survived rendering;
- global old/new occurrence counts have the expected multiset without identifying which owner changed;
- the test file contains an assertion that has not been executed.

Require the ledger evidence to identify the semantic or product owner and map the old observable contract to typed structure, semantic delta, typed outcome, effect, failure order, or actual product behavior in the replacement. For an adaptive transformation, include the relevant movement, unrelated-extension, decoy, ambiguity, drift, post-state, and replay polarity rather than preserving the old textual oracle mechanically.

Exact string evidence remains valid when the text or bytes are themselves the live external contract. Record that rendering, wire, CLI, diagnostic-wording, or generation contract explicitly so it cannot be mistaken for structural coverage.

When removing a brittle test, remove its invalid assertion mechanism only after every live behavior it purported to protect has equal-or-stronger evidence at the real owner. Do not record the mechanism itself as an `intentionally-retired` production contract, and do not claim that a source-string oracle had no value merely because its oracle was weak; first decompose the behavior it attempted to cover.

## Audit one old test at a time

For each `removed` identity:

1. Read the complete baseline test body with `git show "$parity_baseline_oid:<path>"`.
2. Enumerate its observable contracts: inputs, positive result, negative guard, typed error, effect order, exact request shape, byte preservation, idempotency, and cleanup behavior.
3. For each contract, establish whether its owning production capability remains live. Locate an actual replacement by behavior only for live contracts; inspect every candidate body completely.
4. Record the mapping in the closure ledger before editing:
   - old path and test name;
   - live behavior assertions;
   - replacement path and test name or names;
   - assertions that preserve each old contract;
   - strengthened polarities or invariants;
   - deliberately retired behavior and the removed production capability that makes it obsolete.
   - inside `evidence`, the assertion kind, semantic or product owner, and whether execution evidence exists for the replacement.
5. Add a focused replacement only when a live assertion lacks coverage. Never create coverage for a retired mechanism to satisfy the ledger. Rewrite test by test; do not replace a whole file when individual edits can retain attribution.
6. Re-run the inventory after edits and reconcile every remaining `removed` and `globally-missing` row.
7. Run the ledger gate:

```bash
"$CODEX_HOME/skills/verify-test-parity/scripts/verify-test-parity-ledger.sh" --baseline "$parity_baseline_oid" --repo . --ledger /absolute/path/to/test-parity.tsv
```

The gate rejects an omitted removal, a stale baseline identity, a missing replacement, or an intentional retirement without production-capability evidence.

Never accept aggregate test counts, compilation, coverage percentages, a renamed function, or a file move as parity evidence. Do not preserve tests for deleted ghost behavior, but require evidence that the owning production capability itself was intentionally removed. Preserve fixtures and helpers only when a live replacement still needs them.

## Verify the completed ledger

Run the repository's authorized focused tests for each changed owner, then its canonical test gates. Report separately:

- removed tests with direct replacements;
- removed tests split across stronger positive and negative replacements;
- tests moved without behavioral change;
- intentionally retired tests and their retired product behavior;
- any unresolved parity gap.

If a parity gap or disputed capability retirement cannot be resolved without a product decision, stop and ask rather than silently weakening the suite.

## Provenance

This contract is grounded in rollout `019fe1d3-ea48-7de1-91b0-ea98810d1213`, session `~/.codex/sessions/2026/08/08/rollout-2026-08-08T22-43-09-019fe1d3-ea48-7de1-91b0-ea98810d1213.jsonl`: user rule ordinal `8` requires contract-level replacement evidence or capability-specific retirement and permits mixed rows for aggregate tests; ordinals `846–848` record the first successful `test-parity.tsv` creation. Use this only as provenance for the reusable rule, never as a repository-specific baseline or ledger answer.
