---
name: separate-creation-and-enablement
description: "Create and validate an inert artifact while preserving adoption, registration, installation, synchronization, and activation as separately authorized lifecycle stages. Use when a user requests a script, hook, skill, configuration, template, or integration artifact but has not authorized enabling it, or when lack of enablement authority is being used incorrectly as a reason not to create the artifact."
---

# Separate Creation and Enablement

Materialize the requested artifact at the least-active authoritative location, validate it in isolation, and report the separate effects that would make it live. Do not withhold creation merely because activation is unauthorized, and do not smuggle activation into creation.

## Classify the lifecycle stages

Record four distinct states before editing:

1. **Created:** the inert artifact exists at a reviewable path.
2. **Adopted:** an authoritative product or canonical source has selected the artifact.
3. **Registered or distributed:** a loader, installer, synchronization workflow, hook table, manifest, or configuration points to it.
4. **Active:** a runtime or agent can execute or discover it in normal operation.

One user instruction may authorize several states, but never infer a later state from an earlier one. Name the exact transition the user requested.

## Inspect active projections

- Determine whether the intended source path is already linked, imported, watched, generated into active output, or loaded dynamically. Writing an already projected canonical file may activate behavior immediately.
- When only creation is authorized, choose a pending, disabled, example, fixture, or otherwise inert location that still preserves the artifact's intended ownership.
- Do not create a misleading inactive copy when the user explicitly authorized an official-source edit; report its activation consequence and follow the actual authority.

## Create and validate without enabling

- Build the complete artifact rather than stopping at a proposal or pseudocode merely because it is inactive.
- Run direct structural or behavioral validation that does not require registration. Tests may invoke the artifact explicitly from its inert path.
- Keep payload and configuration examples schema-valid so later activation is a separate wiring effect, not another implementation project.
- Prove negative boundaries: no active configuration changed, no loader gained a new reference, no synchronization ran, and no installed projection appeared.

## Hand off activation separately

Report the created path, validation, present activation state, exact future adoption and activation steps, and their side effects. Perform those steps only after explicit user authorization for each affected system.
