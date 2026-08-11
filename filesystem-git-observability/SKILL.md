---
name: filesystem-git-observability
description: "Design and execute auditable filesystem and Git mutations with durable pre/post evidence, production-faithful fixtures, explicit invariant ownership, and condition/expected/received failure diagnostics. Use for bulk repository discovery or mutation, Git config and remote changes, lock-and-rename behavior, refs/object preservation, filesystem metadata investigation, or recovery when execution evidence was not persisted. Do not use to invent ownership/mode/UID/GID gates, copy repository contents implicitly, or replace general command-progress design owned by `$design-command-observability`."
---

# Filesystem Git Observability

Make filesystem and Git effects explainable, repeatable, and resumable. Write the exact operation as a durable script before running it; preserve its parameters and evidence on disk; and report failures as a falsified condition with exact expected and received values.

## Establish the real contract

Before designing a check, separate three categories:

- **User-authorized acceptance invariants:** the exact repository, Git, or filesystem facts that must hold for success, such as removal of named Git config sections, preservation of all other config entries, or continued resolvability of every recorded ref.
- **Behavior-relevant parameters:** facts that can change how the operation behaves and therefore must be represented in fixtures, such as executable/version, argv, environment, effective identity, supplementary groups, umask, parent setgid state, file mode, filesystem device, mount behavior, repository topology, worktree indirection, symlinks, and config-path resolution.
- **Informational observations:** facts worth recording for diagnosis but not authorized as gates.

Never promote an observed attribute into an acceptance invariant merely because it is easy to compare. In particular, mode, owner UID, and group GID are informational for Git's lock-file-and-rename behavior unless the user explicitly makes them part of the task. Git refs, objects, config semantics, and user-named preservation requirements are distinct from incidental filesystem metadata.

State every invariant before the first production mutation. For each one, record its source: explicit user instruction, repository contract, or accepted test. If no source authorizes a check, do not gate on it.

## Scope durable command recording to evidence-producing work

- Read governing instructions and narrowly inspect source directly when the read is not itself an audit artifact. Those passive reads do not require a task-local wrapper merely because they inform later reasoning.
- Use the durable driver and report workflow whenever computed selection, mutation, or collected command output will be relied on as filesystem or Git evidence. Persist the operation, inputs, outputs, status, and interpretation boundary before treating the result as authoritative.
- Convert an ambiguous multi-step shell procedure into durable machinery before execution when its intermediate choices, mutation order, or collected output affect the evidence chain.
- Treat a packaged inspection helper as authoritative when its output participates in preserved evidence. Do not reimplement its selection or parsing ad hoc and then claim equivalent audit provenance.

This boundary does not weaken `$design-command-observability`: add that skill when a command blocks, fans out, needs progress signals, or must preserve a stdout protocol.

## Put all workflow output in `.scratchpad/`

Resolve the canonical `agentic-skills` checkout by its Git remote identity before creating workflow artifacts. Use `<resolved-repo>/.scratchpad/<skill-or-task>/` for scripts written specifically for the task, decision ledgers, command captures, pre/post manifests, fixtures, context excerpts, evidence searches, and validation reports.

Keep reusable packaged scripts under this skill's `scripts/`. Preserve a final task deliverable at an external destination only when that destination is part of the user's task contract; its supporting scratch evidence still belongs in `.scratchpad/`.

Do not copy repository contents into `.scratchpad/` merely to inspect or hash them. A hash walk reads file content; it is not a copy. Report the number of files, directories, roots, and bytes read so the user can distinguish observation from copying. Copy data only when the user authorizes a copy and name the exact source and destination scope first.

## Freeze production parameters before testing

Build a production-parameter matrix before fixture execution. At minimum, capture:

- the exact executable, version, argv, working directory, environment overrides, timeout, and concurrency;
- effective UID/GID, supplementary groups, and umask as behavior inputs rather than implicit success criteria;
- file and parent-directory type, mode, ownership, setgid bit, device ID, mount/filesystem characteristics, and symlink resolution;
- regular repository, bare repository, submodule, linked-worktree, separate-git-dir, and shared-config topology actually present;
- every production code path, option, batch size, serialization path, resume mode, and verifier path.

Partition production inputs into behaviorally distinct classes. A small sample is valid only when it covers every class that can select a different mutator or verifier path.

## Require fixture-to-production parity

Fixtures must call the same mutator function and the same verifier function with the same behavior-relevant parameters used in production. A lookalike command, separately reimplemented check, process-owned fixture, different filesystem, different identity, or reduced option set is not parity.

Persist a mapping from every production class to at least one fixture. For each mapping, record each parameter as `equal`, `intentionally varied`, or `not reproduced`. If a parameter cannot be reproduced, state the exact condition, expected production value/class, received fixture value/class, and the claim that is therefore unavailable. Do not silently generalize fixture results to uncovered production classes.

When testing filesystem behavior from the canonical repository's `.scratchpad/`, compare fixture and production device/mount facts. If they differ, the experiment may explain generic Git behavior but does not establish same-filesystem production behavior.

## Persist the baseline before mutation

The pre-state must survive process failure, context compaction, and a different operator resuming the task. Before the first mutation:

1. Write a versioned manifest containing the exact target inventory, accepted invariants, command parameters, production-class mapping, config semantics, refs, object/repository integrity evidence, and content hashes required by the contract.
2. Flush and `fsync` the file, atomically publish it, then re-read it from its final path.
3. Validate its schema, counts, hashes, and source provenance through the same verifier the production run will use.
4. Record a durable `baseline_ready` barrier. Do not mutate when that barrier is absent or invalid.

Keeping a hash, tuple, or count only in process memory is not a baseline. Printing it to a transient terminal is not a baseline. Computing the real production baseline only after mutation cannot prove historical preservation.

## Execute through one resumable script

Use one durable, parameterized driver for inventory, fixture parity, baseline, mutation, and post-verification, or a small set of durable scripts with an explicit manifest handoff. Do not substitute ad hoc shell loops or one-off commands during production.

The driver must:

- use argument arrays rather than shell interpolation for Git commands;
- record each intended effect before execution and its exit status afterward;
- distinguish `not_started`, `started`, `succeeded`, `failed`, and `verified` states;
- make reruns idempotent or refuse them with an exact state mismatch;
- preserve machine-readable output separately from progress messages;
- stop before any rollback, repair, retry, or broadened mutation not already authorized.

Use `$design-command-observability` in addition to this skill when a command blocks, fans out, needs heartbeat/progress design, or must preserve a stdout protocol.

## Make every failure actionable

Never emit a label such as `config ownership or mode changed` by itself. A failure record must include:

- `event`: stable machine-readable failure name;
- `subject`: repository ID/path and affected config or filesystem path;
- `condition`: the exact predicate evaluated;
- `condition_source`: who or what authorized the predicate;
- `expected`: exact value, set, count, hash, or state;
- `received`: exact observed value, set, count, hash, or state;
- `mismatched_fields`: field-by-field expected/received pairs;
- `effect_state`: what had started or completed before the failure;
- `evidence_path`: durable baseline/report path;
- `next_safe_action`: what can be retried or inspected without broadening authority.

Report command exit status separately from inner assertions. If a diagnostic command exits nonzero, it did not pass even when some assertions inside it succeeded.

## Verify the authorized semantics

After mutation, verify only the accepted contract. For Git-config work this commonly means:

- targeted sections are absent;
- non-target sections and values match the durable baseline;
- refs still resolve to the same object IDs when preservation was required;
- object connectivity and repository access checks succeed for every inventoried topology;
- no unplanned target or config store was touched;
- every per-target result reached a terminal, durably recorded state.

Distinguish historical preservation from current integrity. A clean current `fsck`, readable refs, or correct current config is valuable, but it does not reconstruct a missing pre-mutation baseline. Say exactly which conclusion each evidence set supports.

## Packaged scripts

- `scripts/persist_command_report.py` runs an exact argv without a shell and atomically preserves command, input hashes, timestamps, stdout, stderr, parsed JSON, and exit status.
- `scripts/inspect_source_context.py` atomically writes bounded line-numbered context around exact markers or selected lines; use it instead of ad hoc `sed`/`awk` inspection.
- `scripts/search_execution_evidence.py` performs a bounded marker search over named roots and writes an exclusive JSON report with marker-local excerpts.
- `scripts/analyze_rollout_evidence.py` extracts task-specific runtime markers from one JSONL rollout without copying unrelated conversation content.
- `scripts/investigate_git_config_metadata.py` observes Git-config lock-and-rename metadata behavior in `.scratchpad/` fixtures, compares behavior-relevant parameters, and explicitly keeps metadata out of the acceptance gate.

Run each script from the resolver-selected canonical package and place its generated output under the resolved `.scratchpad/`. Read a script before modifying it, test every changed path directly, and preserve historical reports instead of overwriting them.
