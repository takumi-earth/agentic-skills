# Mixed-Workspace Policy

Load this reference when integration, configuration placement, or validation-command changes can alter the reach of first-party lint or formatting policy. Apply it to the affected boundary; an ordinary lint fix does not require a configuration audit.

## Preserve the selected ownership and layout

Identify first-party crates, upstream-owned crates, and the supported build contexts named by the task. Keep toolchain, edition, and dependency alignment separate from lint and formatting ownership. A generated seam or compatibility patch inside an upstream crate does not transfer that crate's policy ownership.

For a Rust integration whose selected policy requires crate-local configuration, keep Rust and Clippy lint declarations in each first-party crate's `Cargo.toml`, and keep `clippy.toml` and `rustfmt.toml` at the required crate boundary. Do not export those rules through parent `[workspace.lints]` or add upstream inheritance. A nested-workspace root configuration alone does not establish that the intended scope survives integration.

Preserve that explicit layout requirement without imposing it on workspaces with a different selected policy. Route generated or integrated configuration through its designated source owner rather than hand-editing outputs controlled by that workflow.

## Trace effective configuration in supported contexts

For each supported, authorized invocation affected by the change, identify the relevant configuration-discovery inputs: ancestor files, working directory, manifest selection, explicit configuration paths, and environment overrides. Determine what the selected tool and command actually consume; do not infer effective policy solely from filenames or configuration presence.

Inspect standalone and parent-consumed contexts only when each belongs to the supported task surface. Do not add an excluded standalone check, recreate a retired nested workspace, or broaden a parent command merely to complete a two-context matrix.

Do not replace an explicit crate-local requirement with blanket lint flags or a parent-wide formatting command using first-party rules. Preserve the effective policy of upstream crates while retaining the full first-party standard.

## Keep enforcement evidence attributable

When verification is authorized, use evidence that distinguishes first-party enforcement from upstream policy preservation in the selected contexts. Configuration files existing does not prove which rules a command applied; a passing upstream build does not prove first-party enforcement.

Use `$verify-strict-work` for the actual preparation barrier, allowed commands, batch and failure order, and stopping conditions. Do not import a historical complete-round workflow into a task with a different policy. Preserve previously obtained applicable evidence and distinguish deliberately unrun checks according to that owner.

Fix first-party diagnostics structurally without suppressing failures, weakening policy, pinning obsolete dependencies, or imposing first-party rules on upstream code. Required compatibility repairs remain in their authorized scope even when the affected upstream crate follows different lint rules.

Keep findings in the existing response or task record. This reference grants no configuration edits, execution, persistence, or broader policy audit beyond the current task authority.
