# Strict Fixture Owner Integration

## Planning handoff

For each positive and negative scenario, record:

- production artifact role;
- committed repository-relative fixture path;
- whether bytes must be loaded exactly;
- whether extension or filesystem layout affects behavior;
- whether valid or intentionally invalid source is involved;
- typed, parsed, or exact-byte oracle;
- forbidden substitutes;
- explicit non-goals for neighboring fixtures.

An implementation-ready strict plan must not leave these choices to test-helper convenience when they change the production boundary.

## Implementation handoff

Before seeding a scenario:

1. Match each input to the plan's role and fixture path.
2. Load exact bytes for scenario-defining files.
3. Reject helper mutation such as replacement, concatenation, rendering, or marker expansion.
4. Keep source-free cases source-free.
5. Parse final files for semantic assertions unless byte identity is the contract.
6. Preserve positive and negative polarity at the full workflow boundary.

## Protected evidence edge

Treat `fixture file -> production loader -> prepared or executed workflow -> typed outcome` as the evidence chain. Replacing the fixture file with constructed bytes changes the first edge and can conceal path, role, parsing, or materialization defects.

