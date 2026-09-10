---
name: define-codex-goal-artifacts
description: "Specify event-local artifact metadata for Codex goal-tool responses. Use for an explicitly scoped response/protocol design or implementation; this alternative requires attributable invocation input and does not provide durable artifact associations after resume."
---

# Define Codex Goal Artifacts

Attach `managedObjectiveArtifacts` to the selected goal-tool response profile from the same committed goal snapshot and an attributable invocation input. Keep the metadata event-local.

This nested package is a corrected inert specification retained for adoption review. Apply its design only within the user's authorized task; do not silently merge sibling alternatives.

## Load the concrete contract

- Read `references/approach.md` for this variant's responsibility and relationships.
- Read `references/goal-tool-response-schema.md` for exact fields, producer input, invocation/current-goal binding, compatibility, and missing metadata behavior.
- Read `references/source-change-map.md` when the revision-attributed response producer and shared consumer seams affect the task.

## Preserve the distinctions

- An authoritative user-input/attachment designation must reach the producer. Moving objective-prose parsing upstream does not eliminate parsing or create that authority.
- Bind artifacts to the exact response, goal, objective, and live invocation. A replay or timestamp does not establish current authority or authorize another effect.
- Report missing metadata after resume as unavailable. Do not add a hidden durable cache or select a historical response to change this alternative's lifetime.

## Authority and evidence

- Specification maintenance does not authorize editing Codex source, migrating state, registering hooks, changing configuration, promotion, installation, synchronization, or publication.
- Use the existing response or authorized record for diagnostics. Preserve condition, expected/received observations, stage, and code; classification does not require a new persisted audit.
- Present paths beneath the user home as `~/...` at actual path boundaries and preserve original evidence bytes.
- Validate the changed package and evaluate the contract's applicable positive and negative cases locally. Runtime serialization, lifecycle, and compatibility claims require the selected implementation's authorized tests; planned cases and structural validation do not establish execution. Report assertions and process exit status separately.
