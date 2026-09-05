---
name: isolate-first-party-policy-in-mixed-workspaces
description: "Keep first-party lint and formatting standards scoped to their owners when crates are integrated into a larger mixed-ownership workspace. Use for integration policy, configuration placement, or validation-command changes; not for an ordinary lint fix that leaves policy scope unchanged."
---

# Isolate First-Party Policy in Mixed Workspaces

First-party code must satisfy its required quality standard without silently imposing that standard on upstream crates. Integrating a crate changes its build context, not the ownership of every crate around it.

## Separate alignment from policy ownership

Establish which crates are first-party and which remain upstream-owned. Read the selected toolchain, edition, dependency, lint, and formatting policies as distinct requirements.

Authorized toolchain, edition, or dependency alignment may apply across the parent workspace. That does not authorize adopting the first-party lint regime for the parent. A generated seam or compatibility patch inside an upstream crate does not transfer ownership of that crate.

## Keep configuration scope stable after integration

For Rust integrations that require crate-local policy:

- Keep Rust and Clippy lint declarations in each first-party crate's `Cargo.toml`; do not export them through parent `[workspace.lints]` or add upstream inheritance.
- Keep first-party `clippy.toml` and `rustfmt.toml` at the crate boundary required by the selected policy. A nested-workspace root configuration alone may not preserve that scope after integration.
- Trace the actual configuration discovery for both standalone and parent-consumed invocations. Check ancestor files, working directory, manifest selection, explicit configuration paths, and environment overrides.
- Do not use global lint flags or parent-level formatting commands configured with first-party rules as a substitute for proper scope.
- Route generated or integrated configuration through its designated owner; do not hand-edit upstream files when the integration workflow owns them.

Do not infer that every workspace needs this exact layout. Apply the user-selected policy and verify its effective boundary; preserve unrelated local differences.

## Validate both sides of the boundary

When verification is authorized, demonstrate that first-party crates receive their full standard in each supported build context and that upstream crates retain their own policy. Select commands by ownership and supported build surface, not by the convenience of a blanket workspace flag.

Fix first-party diagnostics structurally. Integration difficulty is not permission to weaken their policy, suppress failures, pin obsolete dependencies, or transfer stricter rules onto upstream code. Required compatibility repairs remain in scope even when the upstream crate uses different lints.

Configuration presence alone does not prove effective scope. Conversely, a passing upstream build does not prove that first-party crates were checked under their required rules. Keep those evidence claims separate, and follow the user's preparation and complete-verification-round barriers.
