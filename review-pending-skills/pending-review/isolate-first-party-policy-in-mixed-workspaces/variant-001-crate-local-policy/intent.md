# Crate-local policy in mixed-ownership workspaces

## Origin and intent

On 2026-09-05, the user clarified that first-party `codex-bun` code must meet the strict ecosystem standard while upstream `codex-rs` crates must not inherit that lint regime. The user specifically required per-crate Rust/Clippy lint rules, `clippy.toml`, and `rustfmt.toml`, distinct from workspace-wide edition, toolchain, and dependency alignment. The user then explicitly approved reusable skills reinforcing the confirmed understanding.

This variant targets policy scope during integration and validation-command design. It preserves both requirements: full first-party quality and no upstream policy leakage. It does not prescribe a Rust layout for unrelated ecosystems or treat all patched upstream source as first-party.

## Relationship and risk

`$guard-strict-work` provides the general owner/scope guard. This candidate adds the concrete configuration-discovery and standalone-versus-parent-consumed checks. `$document-strict-work` owns durable wording, not effective lint configuration. The main risk is treating crate-local files as sufficient evidence without checking which configuration the selected command actually loads.

## Written review scenarios

- Positive: move strict first-party crates under a larger upstream workspace. Expect their manifest lints and configuration to retain the same effective scope.
- Regression: align the parent edition and dependencies, then add first-party lints to parent `[workspace.lints]`. Expect the alignment to remain authorized and the lint transfer to be rejected.
- Regression: a first-party check fails after integration. Expect a structural first-party repair, not suppression or a blanket upstream lint-policy change.
- Negative: fix one ordinary lint without changing policy scope. This specialized workflow should not introduce a configuration audit.

These are written scenarios, not executed configuration or independent-agent evidence.

## Artifact and activation boundary

The package remains a nested pending candidate. No promotion, installation, synchronization, lint-configuration mutation, or verification command is authorized by its creation.
