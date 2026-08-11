# Ledger-validator variant

## Concrete intent

Mechanically reject inconsistent evidence ledgers and unsupported behavioral closure claims.

## Approach

Validate JSON rows for stable identity, semantic owner, contract, scope, evidence state, command identity, assertion result, process exit status, evidence locator, timestamp, and closure consistency.

## Preserved nuance

Structural consistency does not prove test adequacy, parity, semantic ownership, or canonical acceptance. `unexecuted` is a valid honest state rather than a failed test.

## Relationships and uncertainty

This executable alternative overlaps `$verify-test-parity` and complements the protocol variant. Review should decide whether TSV support is worth adding in a sibling rather than expanding this JSON contract.
