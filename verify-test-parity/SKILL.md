---
name: verify-test-parity
description: Close every removed-test disposition against a Git baseline and preserve equal-or-stronger behavioral coverage. Use when tests were deleted, renamed, moved, consolidated, or broadly rewritten; when a large diff may have lost assertions; or when Codex must prove that every removed Rust `#[test]` has a refactored replacement unless a production capability was intentionally removed and made the test obsolete.
---

# Verify Test Parity

Build and close a test-by-test behavioral ledger. Treat inventory counts and renamed functions as discovery evidence, never as proof of parity. Accept no unexplained removed test.

## Inventory the change

Run the comparator from the repository root:

```bash
"$CODEX_HOME/skills/verify-test-parity/scripts/compare-test-inventory.sh" --baseline HEAD --repo .
```

When `CODEX_HOME` is unset, use the discovered skill path directly. Use `scripts/list-test-identities.sh` when a normalized baseline or worktree inventory is needed independently.

Interpret the comparator categories as follows:

- `removed`: a baseline path/name identity is absent from that path in the worktree.
- `moved-candidate`: the removed name exists under another worktree path; inspect both bodies because a matching name does not prove a faithful move.
- `globally-missing`: the old name exists nowhere in the worktree; locate a semantic replacement or identify an intentionally retired product behavior.
- `added`: a worktree path/name identity was absent from the baseline; it may be a replacement, a split polarity, or unrelated new coverage.

The scripts lexically discover Rust functions carrying `#[test]` or a namespaced `...::test` attribute. Supplement them with `git diff --name-status <baseline>` and targeted diff inspection for deleted test files, doctests, macro-generated cases, snapshots, diagnostic fixtures, and non-Rust suites.

## Create the closure ledger

Maintain a tab-separated ledger with this exact header:

```text
baseline-path	test-name	disposition	replacement-path	replacement-test	production-capability-removal	evidence
```

Use one or more rows per removed baseline identity, with one row per independently observable old behavior:

- Use `replaced` when live behavior remains. Name one existing replacement per row, set `production-capability-removal` to `-`, and use `evidence` to map the old observable assertions to that replacement. Multiple rows may map a former aggregate test to stronger split-polarity tests.
- Use `intentionally-retired` only when production capability was deliberately removed and therefore made the old behavior obsolete. Set both replacement fields to `-`, name the removed production command/API/format/workflow in `production-capability-removal`, and cite its source or diff evidence in `evidence`.

An old aggregate test may have both row kinds when some behavior remains under refactored tests while a distinct production capability was removed. Do not retire the whole test merely because one assertion became obsolete.

Do not use retirement for a refactor, rename, changed implementation strategy, currently failing behavior, or difficult fixture. Those still require replacement coverage.

## Audit one old test at a time

For each `removed` identity:

1. Read the complete baseline test body with `git show <baseline>:<path>`.
2. Enumerate its observable contracts: inputs, positive result, negative guard, typed error, effect order, exact request shape, byte preservation, idempotency, and cleanup behavior.
3. Locate the actual replacement by behavior, not only by name. Inspect every candidate body completely.
4. Record the mapping in the closure ledger before editing:
   - old path and test name;
   - live behavior assertions;
   - replacement path and test name or names;
   - assertions that preserve each old contract;
   - strengthened polarities or invariants;
   - deliberately retired behavior and the removed production capability that makes it obsolete.
5. Add a focused replacement when any live assertion lacks coverage. Rewrite test by test; do not replace a whole file when individual edits can retain attribution.
6. Re-run the inventory after edits and reconcile every remaining `removed` and `globally-missing` row.
7. Run the ledger gate:

```bash
"$CODEX_HOME/skills/verify-test-parity/scripts/verify-test-parity-ledger.sh" --baseline HEAD --repo . --ledger /absolute/path/to/test-parity.tsv
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
