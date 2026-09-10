---
name: define-codex-goal-artifacts
description: "Specify durable artifact associations for Codex goal state and protocol projections. Use for an explicitly scoped goal-persistence design or implementation requiring exact artifact roles across lifecycle changes; keep status authority and file effects separate."
---

# Define Codex Goal Artifacts

Persist a versioned `managedObjectiveArtifacts` association with the exact goal and objective revision. Preserve it across status changes; explicitly replace or clear it when the objective changes.

This nested package is a corrected inert specification retained for adoption review. Apply its design only within the user's authorized task; do not silently merge sibling alternatives.

## Load the concrete contract

- Read `references/approach.md` for this variant's responsibility and relationships.
- Read `references/thread-goal-artifact-schema.md` for exact fields, designation provenance, current/historical/output roles, and managed or caller-designated locators.
- Read `references/persistence-migration.md` when atomic state updates, legacy migration, resume/fork behavior, and revision-attributed source seams affect the task.

## Preserve the distinctions

- Distinguish unknown legacy association, known no-file selection, invalid metadata, and a selected file that is currently unavailable.
- Allow any exact user-designated pathname and preserve its established relative base. A stored reference or role does not prove authority, existence, or permission to restore a file.
- Keep goal identity, objective revision, status, accounting, and file availability distinct. Preserve the existing user-owned goal completion decision.

## Authority and evidence

- Specification maintenance does not authorize editing Codex source, migrating state, registering hooks, changing configuration, promotion, installation, synchronization, or publication.
- Use the existing response or authorized record for diagnostics. Preserve condition, expected/received observations, stage, and code; classification does not require a new persisted audit.
- Present paths beneath the user home as `~/...` at actual path boundaries and preserve original evidence bytes.
- Validate the changed package and evaluate the contract's applicable positive and negative cases locally. Runtime serialization, lifecycle, and compatibility claims require the selected implementation's authorized tests; planned cases and structural validation do not establish execution. Report assertions and process exit status separately.
