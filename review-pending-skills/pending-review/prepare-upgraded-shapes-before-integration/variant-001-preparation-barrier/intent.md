# Dependency preparation before integration seams

## Origin and intent

On 2026-09-05, the user clarified that first `codex-bun` `apply` must align Rust/toolchain policy, upgrade dependencies through the prescribed Cargo commands, apply upgrade repairs, and only then apply integration seams written for the repaired shapes. Final dependency/lock convergence precedes checks, Clippy, and tests. The user rejected conservative `cargo update --workspace` as a substitute and explicitly approved skills reinforcing this understanding.

The distinct responsibility is preserving prepared input state across dependency-tool effects and deterministic source transformations. This variant does not make every inventory job spawn Cargo, turn diagnostics into an automatic patch specification, or claim atomic rollback across external commands.

## Relationship and risk

`$protect-causal-architecture` owns disputed authority edges, while this candidate applies a selected preparation chain. `$guard-strict-work` supplies command scope and verification authority. The main risks are over-triggering for a simple lock update and mistaking an example Cargo policy for a universal dependency requirement; the description and conditional command guidance exclude both.

## Written review scenarios

- Positive: first integration requires a newer edition and incompatible dependency updates. Expect the public workflow to prepare and repair the parent before planning seams.
- Regression: dependency maintenance changes manifests and the lockfile, but a cached source index survives. Expect a fresh planning input epoch before any dependent edit.
- Regression: a later source transaction fails after Cargo changed the parent. Expect accurate earlier-effect reporting, not a false whole-workflow rollback claim.
- Regression: a partial compile repair is followed by a focused rerun despite a complete-round requirement. Expect the rest of the issue batch to be implemented first.
- Negative: the user requests explanation or documentation only. No dependency, integration, verification, or installation command should run.

These are written scenarios, not executed workflow or independent-agent evidence.

## Artifact and activation boundary

This variant remains nested and pending. Creating it does not promote, install, synchronize, register, or execute it. No scripts are included.
