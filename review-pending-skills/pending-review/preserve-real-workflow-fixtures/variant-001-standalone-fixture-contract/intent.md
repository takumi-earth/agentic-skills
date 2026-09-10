# Standalone fixture-contract variant

## Concrete intent

Require workflow and integration tests to preserve the real on-disk role, provenance, and toolchain treatment of every scenario-defining artifact.

## Approach

Classify inputs by production role, preserve committed exact-byte fixtures when the actual scenario requires them, distinguish valid source from inert invalid snippets, and separate semantic oracles from input construction. Permit faithful parser values, temporary files, and controlled mutation while honoring explicit fixture obligations.

## Preserved nuance

Role-specific files remain distinct even when byte-identical. The contract does not demand fixture files for every parser string, broaden one touched scenario into repository-wide migration, or eliminate compile-fail files when full compiler integration is the behavior under test.

## Relationships and uncertainty

Retain this language-neutral, standalone trigger for comparison; its approved corrections are applied. The user approved folding the corrected `variant-002-strict-owner-reference` into `implement-strict-work/references/workflow-fixtures.md`, with a narrowly scoped planning pointer from `$plan-strict-work`, and pruning that draft. The optional strict-owner guidance does not replace this broader trigger or approve its adoption.

## Applied correction contract

- Narrow blanket committed-file and runtime-construction rules to the actual scenario contract. Preserve explicit requirements for dedicated role-specific files and unchanged starting bytes without imposing them on every filesystem test.
- Preserve small parser strings, tokens, IR, temporary crates, and controlled fixture mutation where they test the contract appropriately; distinguish valid tool-consumed source from inert invalid parser data.
- Preserve role identity, source-free scenarios, independent semantic oracles, and touched-scenario scope. Planning must settle load-bearing identity requirements without requiring every routine filename in advance.
- Retain the corrected standalone trigger as an alternative; promotion and enablement remain separate decisions.
