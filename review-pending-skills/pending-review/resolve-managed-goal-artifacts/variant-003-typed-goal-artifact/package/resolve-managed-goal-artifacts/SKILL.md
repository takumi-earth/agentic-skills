---
name: resolve-managed-goal-artifacts
description: "Specify typed goal-artifact selection for a chosen Codex producer profile. Use when integrating durable or response-local artifact metadata with the shared resolver; preserve exact user paths, role authority, and the selected producer lifetime."
---

# Resolve Managed Goal Artifacts

Consume exactly one selected typed producer profile and verify its current goal/event binding before selecting a file. A role declaration, an old response, or transport success alone does not establish current authority.

This nested package is a corrected inert specification retained for adoption. Its producer profiles are proposed contracts, not fields guaranteed by the running Codex binary.

## Load the concrete contract

- Read `references/approach.md` for this variant's responsibility and relationships.
- Read `references/typed-goal-artifact-contract.md` and its selected producer reference before applying schema or selection rules.
- Read `references/migration-and-resume.md` when compatibility, missing authority, or lifecycle behavior matters.

## Preserve selection and ownership

- Keep durable goal associations distinct from event-local observations. Use the selected producer's exact schema, presence, and lifecycle contract; do not infer a model from a version number or combine both fields.
- Validate every record and its role/cardinality before selecting the sole current artifact. Invalid or unsupported metadata must not silently become objective-prose inference.
- Allow any exact user-designated pathname, including external and relative paths under an established base. Managed attachment shape is not a universal goal-file requirement.
- Keep typed selection and filesystem validation in `$maintain-living-goal`; preserve the existing hook consumers and their output/silence contracts.

## Authority and evidence

- Apply only the user-authorized task. Specification maintenance does not authorize source implementation, goal changes, hook registration, configuration, promotion, installation, synchronization, or publication.
- Use existing responses or authorized records for condition, expected/received, stage, code, and selection-source diagnostics. Classification does not authorize execution or a new persisted audit.
- Normalize home paths as `~/...` at actual component boundaries while preserving original input bytes and file identity.
- Validate the changed package and evaluate relevant positive and negative contract cases locally. Structural validation and written scenarios do not establish a working producer, live hook event, cross-platform execution, or migration. Report assertions and process exit status separately.
