---
name: verify-test-parity
description: "Audit behavioral parity across a broad or explicitly requested test rewrite. Use when the user asks for comprehensive removed-test accounting or a closure ledger, when many tests changed and local mappings cannot establish whether behavior was lost, or when a disputed capability retirement needs Git-backed proof. Do not invoke for isolated test edits, merely because tests are brittle, or because a stale plan mentions parity."
---

# Verify Test Parity

Preserve live behavior without making a repository-wide audit the default implementation workflow.

## Choose the smallest sufficient mode

Use one of two modes:

- **Touched-test mapping:** use during ordinary implementation when a bounded set of tests is deleted or rewritten. Map only the observable contracts being touched; do not run a global inventory or create a durable ledger by default.
- **Comprehensive audit:** use only when the user requests complete removed-test accounting or local mappings cannot resolve a broad parity risk. Use the comparator and ledger validator in this package.

Do not invoke this skill merely because another plan mentions it. Do not turn removal of one brittle source-string assertion into a baseline-selection project.

## Map touched tests during implementation

For each touched test:

1. Define the current production or product contract before reading historical test mechanics.
2. Add equal-or-stronger evidence at the real owner.
3. Use `git show <ref>:<path>` only when the old test may contain another observable contract.
4. Split aggregate tests into independently observable positive, negative, preservation, ordering, idempotence, cleanup, and side-effect assertions.
5. Mark each contract `replaced` or `intentionally-retired`.

Use `replaced` only for a still-live behavior with executed replacement evidence. Use `intentionally-retired` only when the owning production command, API, format, workflow, or effect was actually removed. Removing a brittle oracle, renaming a test, or changing implementation strategy does not retire behavior.

Keep the mapping inline, in the existing plan, or in an already-required task artifact. Do not create a new scratch report solely because the skill triggered.

## Select an audit ref only for comprehensive mode

For a comprehensive audit, use the Git ref named by the user or task. If none was named and implementation started from an unambiguous pre-edit `HEAD`, use that starting commit as the archive ref. Ask only when competing refs would materially change which behaviors are in scope.

Resolve the chosen ref once to an OID and pass it consistently to the audit commands. Do not move the ref forward to reduce the removed-test set.

Run the comparator from the repository root:

```bash
audit_baseline_oid='<resolved audit OID>'
"$CODEX_HOME/skills/verify-test-parity/scripts/compare-test-inventory.sh" --baseline "$audit_baseline_oid" --repo .
```

Use `scripts/list-test-identities.sh` only when an independent normalized inventory is useful. The scripts lexically discover Rust functions carrying `#[test]` or a namespaced test attribute; inspect deleted files, doctests, macro-generated cases, snapshots, diagnostics, and non-Rust suites only when they are in the requested audit scope.

Interpret inventory categories as discovery evidence:

- `removed`: absent at the same path and name;
- `moved-candidate`: same name elsewhere, requiring behavioral inspection;
- `globally-missing`: no same-name worktree test;
- `added`: possible replacement, split polarity, or unrelated coverage.

Counts and matching names do not prove parity.

## Use a closure ledger only for comprehensive mode

Use this exact TSV header with the provided validator:

```text
baseline-path\ttest-name\tdisposition\treplacement-path\treplacement-test\tproduction-capability-removal\tevidence
```

Use one row per independently observable contract:

- For `replaced`, name an existing replacement test, set `production-capability-removal` to `-`, and identify the semantic or product owner plus executed assertion evidence.
- For `intentionally-retired`, set replacement fields to `-`, name the removed production capability, and cite source or approved architecture evidence.

Never invent a substitute test to make the ledger pass. A test of the new architecture is not a replacement for a deliberately retired old mechanism unless it also proves a still-live observable contract.

For adaptive source transformations, rendered substrings, snapshots, copied bodies, parse-then-text assertions, markers, global occurrence counts, and unexecuted test source do not establish replacement parity. Use `$test-adaptive-source-transforms` for typed ownership, movement, decoy, ambiguity, drift, post-state, and replay evidence.

Run the ledger gate after recording all in-scope removals:

```bash
"$CODEX_HOME/skills/verify-test-parity/scripts/verify-test-parity-ledger.sh" \
  --baseline "$audit_baseline_oid" \
  --repo . \
  --ledger /absolute/path/to/test-parity.tsv
```

The gate validates inventory coverage and referenced test identities. It does not prove semantic equivalence; establish that through executed owner-level tests.

## Report only useful distinctions

After authorized focused and canonical tests run, report:

- live contracts with direct or split replacements;
- intentionally retired contracts and their removed production capabilities;
- unresolved parity gaps.

Do not pad the report with aggregate counts, historical rollout narration, or a list of unchanged tests.

Stop only when a live contract lacks evidence or a capability retirement requires a product decision. Otherwise continue implementation.
