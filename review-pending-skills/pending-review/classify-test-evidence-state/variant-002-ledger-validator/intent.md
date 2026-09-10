# Ledger-validator variant

## Concrete intent

Mechanically reject inconsistent evidence ledgers and unsupported behavioral closure claims.

## Approach

Validate JSON rows for stable identity, semantic owner, contract, scope, evidence state, command identity, assertion result, process exit status, evidence locator, timestamp, and closure consistency.

## Preserved nuance

Structural consistency does not prove test adequacy, parity, semantic ownership, or canonical acceptance. `unexecuted` is a valid honest state rather than a failed test.

## Relationships and uncertainty

Retain this corrected executable alternative pending adoption. It overlaps `$verify-test-parity`; its general evidence distinctions now belong to `$verify-strict-work` and `$maintain-living-goal`. The approved `variant-001-evidence-state-protocol` was folded into those owners with corrected attribution and authority rules, then pruned. Its complement relationship is historical.

The owners classify available evidence in the existing response or authorized record. They do not require this validator or authorize creating a ledger. Structural validation of caller-supplied rows does not establish source/configuration/run identity, test adequacy, or canonical acceptance. Whether TSV support warrants a sibling remains an unresolved design choice.

## Applied correction contract

- Preserve the declared structured error contract for wrong-shaped enum values and invalid UTF-8 input; malformed values and invalid UTF-8 now produce the declared JSON failure result.
- Validate calendar timestamps, not only their textual shape, and reject Boolean `schema_version` values that Python otherwise equates with `1`.
- Enforce the declared evidence-locator requirement for written rows; a null locator is reserved for merely declared evidence.
- Preserve exact command arguments, including legitimate empty arguments after the executable; rejecting them loses valid command identity.
- Reconcile gate states with assertion results and declared acceptance criteria. Passing gates require explicit passed acceptance criteria and reject failed assertions even when behavioral closure is false; process success alone cannot establish gate acceptance.
- Normalize paths beneath the home directory as `~/...` in input errors and diagnostics, and prevent uncaught tracebacks from bypassing the structured response.

These approved repairs are applied in the package and covered by direct tests. Compilation observes a build command, not test-body execution. Adoption and enablement remain separate decisions.
