# Authority topology contract

## Required authorities

Keep these roots independent:

| Authority | Source | Permitted use | Forbidden inference |
| --- | --- | --- | --- |
| Package resources | Invoked package location | Read resources shipped with the package | Harness state or canonical repository identity |
| Harness state | Explicit argument or inherited environment | Read harness-owned configuration and state | Resolved `__file__` parents |
| Canonical repository | Explicit caller selection | Read canonical repository-owned state | Copied or linked package parent |
| Task output | Validator-owned disposable root | Write declared fixture output | Package, harness, repository, or external paths |

## Fixture topology

Execute the target package directly, as a complete copy, through a relative directory symlink, and through an absolute directory symlink. When the target declares sibling-package dependencies, reproduce every dependency as a copy or the corresponding relative or absolute symlink in the same lexical fixture repository.

Use identical target arguments and explicit authorities across all four rows. Normalize only topology-specific package and task-output paths before comparing target JSON. Never normalize an authority mismatch into parity.

## Negative evidence

- Omit runtime authority and require failure without parent walking.
- Omit a declared sibling from copied and linked fixture repositories and require failure.
- Execute a target that derives runtime state from `Path(__file__).resolve().parents[...]` and require parity failure.
- Require every declared side effect beneath the disposable task-output root.
- Hash the canonical repository and runtime root before and after the matrix and require both unchanged.
