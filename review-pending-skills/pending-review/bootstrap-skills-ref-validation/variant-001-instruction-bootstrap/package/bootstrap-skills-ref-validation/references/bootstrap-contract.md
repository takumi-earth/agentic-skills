# Skills-ref bootstrap contract

## Resolve

1. Read repository validation guidance and the declared pinned-reference layout.
2. Distinguish distribution `skills-ref`, import `skills_ref`, CLI `skills-ref`, and source directory.
3. Inspect source package metadata, version, dependencies, and helper interpreter declarations.
4. Check installed CLI and module provenance independently.

## Plan

When required tooling is absent, report:

- exact pinned source;
- intended install command and environment;
- dependency and network effects;
- import, CLI, source-cleanliness, and validator checks;
- whether escalation would be required for the intended command.

Do not execute the plan without explicit environment-mutation authority.

## Verify

- Confirm the import origin and declared version.
- Confirm the CLI surface or version.
- Confirm the pinned source was not modified to make validation pass.
- Invoke Python helpers with Python when their executable bit is absent.
- Run and report canonical and harness-specific validators separately.

Missing tools, invalid pinned source, mismatched provenance, command failure, inner assertion failure, and nonzero process status are distinct outcomes.
