---
name: define-codex-goal-artifacts
description: "Specify a trusted runtime-root extension for Codex PostToolUse consumers. Use for an explicitly scoped runtime-context protocol design or implementation; this alternative does not identify a goal artifact or supply durable goal associations."
---

# Define Codex Goal Artifacts

Supply a versioned `runtime_context.codex_home` from the session runtime. This resolves runtime location only; artifact identity and user designation remain separate.

This nested package is a corrected inert specification retained for adoption review. Apply its design only within the user's authorized task; do not silently merge sibling alternatives.

## Load the concrete contract

- Read `references/approach.md` for this variant's responsibility and relationships.
- Read `references/post-tool-use-schema.md` for field types, trusted namespace/home binding, event/environment precedence, and input-profile compatibility.
- Read `references/source-change-map.md` when the inspected producer and consumer integration seams affect the task.

## Preserve the distinctions

- Treat absent legacy context differently from a missing negotiated field, present `null`, invalid data, and unsupported versions. Invalid authority never triggers a fallback.
- Preserve custom roots and component-boundary home normalization. Package location is not runtime authority; copied events cannot redefine the consumer's home.
- Select compatible handler profiles before emitting new fields. Recompute context for the runtime performing a supported resume or fork.

## Authority and evidence

- Specification maintenance does not authorize editing Codex source, migrating state, registering hooks, changing configuration, promotion, installation, synchronization, or publication.
- Use the existing response or authorized record for diagnostics. Preserve condition, expected/received observations, stage, and code; classification does not require a new persisted audit.
- Present paths beneath the user home as `~/...` at actual path boundaries and preserve original evidence bytes.
- Validate the changed package and evaluate the contract's applicable positive and negative cases locally. Runtime serialization, lifecycle, and compatibility claims require the selected implementation's authorized tests; planned cases and structural validation do not establish execution. Report assertions and process exit status separately.
