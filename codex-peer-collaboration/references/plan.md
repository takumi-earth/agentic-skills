# Codex peer collaboration: living plan

Last materially updated: `2026-10-03`, `Asia/Hong_Kong`.

This is the maintained project record requested by the user, outside the Codex checkout. Keep this file current rather than creating parallel plans. [Runtime investigation](runtime-investigation.md) owns the detailed source findings.

## User-selected objective and decisions

The user wants existing independent sessions they directly interact with and monitor to discover one another, communicate proactively, retrieve replies, and delegate bounded work.

The required client and host combinations are:

1. Ubuntu sessions collaborating while the user operates them through the Mac desktop app.
2. Mac sessions and Ubuntu sessions collaborating with each other while the user monitors both through the desktop app.
3. The same collaboration while the user connects through the ChatGPT phone app to the desktop app. The user reports that phone access to sessions on both hosts already works.
4. Continued use of the source-built Codex CLI/TUI on both Mac and Ubuntu.
5. Minimize recurring effort to pull upstream changes and carry the peer feature forward, while preserving the selected architecture and correctness.

The selected architecture is one enhanced Codex fork, built for each platform, with peer collaboration owned by the app-server runtime. Each host has its own runtime, session state, and filesystem. Desktop and TUI clients attach to the appropriate runtime; the two runtimes exchange peer messages through an authenticated connection.

Authority provenance is the actual user statements in session `01a0f6cc-3471-74bd-ac52-cf42b069b52a`:

- The user distinguished authorized peer communication/delegation from subagent delegation, which requires explicit requests.
- The user requested a shared enhanced Codex repo and its app-server in both locations, with the desktop app using their own primary runtime.
- The user stated that the desktop app has no such UI configuration and explicitly directed source investigation.
- The user requested durable documentation outside the Codex repo, then explicitly requested a new skill with the plan in its references.
- The user requested an approach with the minimum practical overhead for updating upstream Codex and reapplying the changes.

These decisions are protected project requirements. Reopen them only when the user changes the requirement or a concrete incompatibility needs their decision. Assistant proposals and status do not create new authority.

## Scope and boundaries

- Peer permission covers relevant existing independent sessions. An existing child is not a peer.
- Spawning, creating, or forking sessions and delegating to subagents require explicit user requests.
- Peer assignments retain the recipient's objective, ownership, verification restrictions, model selection, and approval boundaries.
- Peer messages carry authenticated sender provenance and remain tool-originated context rather than human instructions.
- Approve peer exchanges separately from other actions. The recorded global policy is `approval_policy = "on-request"` with `approvals_reviewer = "user"`.
- Source changes, builds, verification, installation, service restarts, runtime activation, staging, commits, and pushes follow the authority for the current phase. This document does not authorize them.
- Earlier suggestions for a separately configured peer MCP service were planning alternatives. The user subsequently selected runtime ownership in the shared Codex fork; do not silently restore the earlier architecture.

## Working roots and baseline

| Item | Recorded value |
| --- | --- |
| Authoritative Ubuntu Codex source | `~/rust-forks/codex-orig`; Rust workspace `codex-rs/` |
| Source checkpoint inspected | `rust-v0.159.2`, Git `HEAD` `ff6aec96948b70d94983af2641a6b67c94faeff5`, with the user's existing patch and peer-approval edits |
| Latest audited release upgrade | `rust-v0.160.0`, Git `HEAD` `a956835d020762cb2b570053af06f643a11c0ecc`; matching CLI and Code Mode host installed on Ubuntu |
| Canonical skill source | `~/agentic-skills/codex-peer-collaboration` |
| Mac source checkout and active local backend | Not yet established by on-host evidence |
| Conversation provenance | `01a0f6cc-3471-74bd-ac52-cf42b069b52a` |

The similarly named checkout `~/rust-forks/codex/codex-rs/bun` belongs to separate Codex-Bun work. It was not the authoritative source for this installation.

## Current requirement state

| Requirement or lane | State and evidence |
| --- | --- |
| Standing peer permission and subagent distinction | Added to `~/.codex/AGENTS.md` in the earlier work; user supplied the policy again in this conversation |
| TUI peer-message approval setting | Carried unchanged, built, installed, and retained in the `0.160.0` successor patch |
| Shared-runtime local peer tools | Not implemented; current `collaboration` tools expose only the current agent tree |
| Package selection and pinning | Confirmed in source; complete local packages can be selected with `update --from-cli` |
| Ubuntu desktop connection | Observed using the source-built `0.159.2` app-server on the shared Unix socket at the `2026-10-02` checkpoint; the `0.160.0` upgrade installs binaries without activating or verifying a new client runtime |
| Mac desktop attachment to our selected runtime | Unverified; no UI selector is available or required as an investigation prerequisite |
| Mac-Ubuntu peer routing | Not implemented |
| Phone use of native peer tools | Not verified; current phone access to both hosts is user-reported existing behavior |
| Durable skill and plan | Created in canonical source; the Codex skill projection resolves there; prior structural validation and Ubuntu synchronization are recorded, with release retention and publication owned by the current upgrade workflow |
| Low-overhead upstream maintenance | Objective requested by the user; the strategy in `upstream-maintenance.md` is proposed and has not been implemented |

## Completed patch checkpoint

The earlier patch adds `tui.peer_message_approval_mode`. The user selected `"approve"` for peer sends, while session creation/forking and other approvals keep their existing rules.

- External successor: `~/rust-forks/codex-v0.159.2-peer-messages.patch`.
- Retained successor: `~/agentic-skills/upgrade-codex-patch/assets/patches/codex-v0.159.2-peer-messages.patch`.
- Both artifacts were rechecked at this documentation checkpoint: `129701` bytes, SHA-256 `d50d1f0c2e6b723b3c4c2e589a54776af0070a830a3ed334338b2f63ee021f46`.
- Retention/publication commit: `b59eb16f0559b0584e37f7475b97680b2a74a368`.
- The upgrade/install sequence completed `cargo upgrade --recursive --verbose`, `cargo update --recursive`, `cargo install --path cli`, and `cargo install --path code-mode-host`.
- Rust lifecycle tests were written but not executed under that upgrade's restricted command contract. Build/install success is not end-to-end approval evidence.
- Intrinsic upgrade evidence is under `~/agentic-skills/.scratchpad/upgrade-codex-patch/20261001T095604Z-peer-messages/`.

The later native-peer work must retain this lineage in a successor patch without overwriting predecessor artifacts.

## Latest release upgrade checkpoint

The user invoked `$upgrade-codex-patch $codex-peer-collaboration` on `2026-10-03`. This phase carries the existing peer-approval lineage onto the selected release and preserves the native-peer implementation and client acceptance work below.

- Target: `rust-v0.160.0`, base `a956835d020762cb2b570053af06f643a11c0ecc`, in `~/rust-forks/codex-orig`. The checkout and index were clean before application; the base and index stayed unchanged.
- Predecessor: `~/rust-forks/codex-v0.159.2-peer-messages.patch`, identical to its packaged resource, SHA-256 `d50d1f0c2e6b723b3c4c2e589a54776af0070a830a3ed334338b2f63ee021f46`. Forward application succeeded without rejects; all initial carried edit streams were identical across `55` files.
- Successor: `~/rust-forks/codex-v0.160.0.patch`, retained byte-identically at `~/agentic-skills/upgrade-codex-patch/assets/patches/codex-v0.160.0.patch`. SHA-256 `cd4d8060ee4f43877f64483e0d3502f2a4151f5921a4027bd1dd94cfbd4ee555`; `130190` bytes, `3262` lines, `56` paths, `193` hunks.
- Comparison: `191` carried hunk edit streams are identical. One dependency hunk upgrades `insta` from `1.48.0` to `1.49.0` and `libc` from `0.2.189` to `0.2.190`; one new manifest hunk pins `cc`. No carried peer-approval edits were removed or rewritten.
- Build remediation: both initial installers failed because `cc 1.6.0` snapshots compiler environment variables before `aws-lc-sys 0.45.0` applies its jitter entropy `CFLAGS` guard. Pin `cc = "=1.2.55"` in `codex-rs/utils/rustls-provider/Cargo.toml`, using the target's original lockfile version. `cargo update --recursive` selected that pin, and both installer retries succeeded. The carried workspace pins for `blake3`, `time`, and `zune-core` remain intact.
- Installations: successful Cargo output confirms `codex`, `logs_client`, and `codex-code-mode-host` at `0.160.0`. The CLI retry took `1238.677` seconds; the Code Mode host retry took `136.728` seconds. Compiler warnings remain recorded in the complete logs.
- Artifact audit: cached forward applicability and reverse applicability both passed separately with exit `0`; predecessor preservation, base/index preservation, intended-path accounting, and exact Git-export bytes passed. `codex-rs/Cargo.lock` changed during dependency resolution and remains excluded from the artifact. Installer retries changed no tracked or untracked source paths.
- Evidence: `~/agentic-skills/.scratchpad/upgrade-codex-patch/20261003T062435Z-v0.160.0-peer/` contains the baseline, phase and per-command snapshots, comparisons, final audit, and complete command streams/status/durations. Only the four authorized Cargo command forms were used, including resolution and installer retries. Rust tests, formatting, linting, and generators were outside this upgrade's command contract.
- Runtime boundary: at this upgrade checkpoint, app-server process `14761` runs `/xdg/cargo/bin/codex (deleted)` and Code Mode host process `1157247` runs `/xdg/cargo/bin/codex-code-mode-host (deleted)` after binary replacement. This phase performs no daemon restart or runtime activation; installation does not establish desktop, Mac, cross-host, or phone acceptance.

The next unfinished project actions remain the native local peer boundary/implementation and Mac attachment investigation. Preserve the selected runtime ownership and the acceptance matrix below.

## Causal chains to preserve

Current TUI-owned chain:

`TUI startup -> ephemeral codex_tui MCP listener -> per-thread config override -> app-server MCP call -> TUI handler -> app-server thread API`.

The listener is disposed when its TUI owner is dropped. A loaded app-server thread can preserve prior overrides while active or observed by another client. That can leave a stale endpoint and policy after a TUI relaunch. The desktop connection inspected later had no `codex_tui` server attached.

Selected target chain:

`selected fork package -> app-server startup -> runtime-owned peer registry/policy/tool registration -> client session -> attributed local peer delivery`.

For remote peers:

`sender runtime context -> qualified host/thread target -> authenticated runtime connection -> receiving runtime admission and delivery -> durable receipt/reply -> sender`.

Package activation must establish the selected executable and matching helper before claiming that a client uses the fork. A daemon's selected package, its running process, the desktop's connection, and the model-visible peer inventory are distinct observable states.

Counterfactual regressions to prevent:

- Moving delivery back into a TUI listener makes desktop-only peer tools unavailable and restores listener-lifetime failures.
- Expanding subagent-tree operations to every session erases the user's peer/child authorization distinction.
- Falling back to human-input delivery misrepresents peer authority.
- Treating plugin/helper paths as the desktop backend selector claims activation without evidence.
- Retrying an ambiguous send without receiver duplicate protection can repeat an assignment.

## Next unfinished work

Mac attachment investigation and the native peer boundary/local implementation can progress independently within the current phase's authority. Do not make a missing Mac probe or UI control a prerequisite for source work that does not depend on it.

Design the peer boundary using [the upstream maintenance strategy](upstream-maintenance.md): keep substantive behavior in owned code, maintain a small inventory of upstream integration points, and evaluate semantic reapplication before creating another patch engine. Minimal maintenance effort cannot justify moving the feature out of runtime ownership or weakening delivery and authorization behavior.

1. **Establish Mac attachment through source-defined runtime interfaces.** Trace or observe which executable, package, socket, and transport the Mac desktop app actually uses. Exercise the selected managed-daemon/package path with proportionate authority. Verify whether desktop startup reuses it or creates a separate backend. Use process/socket evidence, not a requested UI selector or an invented config key.
2. **Finalize the native local peer boundary.** Choose the focused runtime component and thin integration with the session registry and tool pipeline. Keep peer operations separate from child control. Define eligible-session discovery, bounded reads/waits, sender attribution, approval policy, delivery receipts, and duplicate handling.
3. **Implement and prove local peer collaboration.** Establish runtime-owned model tools for desktop and TUI sessions, including an Ubuntu-to-Ubuntu desktop exchange with no TUI listener dependency.
4. **Build and select matching Mac/Ubuntu runtime packages.** Record source/build provenance, complete-package validation, matching Code Mode host, running daemon identity, and actual desktop attachment. Preserve the app's existing integration-resource ownership.
5. **Add cross-host collaboration.** Introduce authenticated host enrollment and qualified session identities over the existing SSH route or another explicitly selected transport. Define disconnected and uncertain-delivery outcomes.
6. **Verify the full client matrix and retain the successor.** Complete the acceptance evidence below, update this record, and use `$upgrade-codex-patch` when its retention/build/publication phase is authorized.

These are planned actions. Continue only the next effect authorized by the current user request.

## Acceptance evidence still required

- Desktop discovery, messages, replies, and bounded assignments between existing Ubuntu peers with no TUI-owned endpoint.
- Equivalent local-peer behavior on Mac using the selected forked runtime.
- Mac-to-Ubuntu and Ubuntu-to-Mac exchanges, with host-qualified identity and visible provenance.
- Delivery to idle and active peers without changing the recipient's objective or settings.
- Reconnect/restart behavior with correct receipts and no silent duplicate delegation.
- Peer exchanges use the selected approval policy; unrelated actions retain their approvals; creating/spawning/forking still follows explicit-user-request requirements.
- A peer message remains tool-originated context in model input and persisted history.
- The same operations are available while the user controls the desktop sessions from the phone.
- Report written, compiled, executed, and end-to-end evidence separately.

## Open questions

- Does the Mac desktop app use the standard control socket/managed daemon for local sessions, or a separately launched primary-runtime backend?
- Which package/connection integration point lets the app use our build durably without relying on a nonexistent UI selector?
- Does the existing tool-output API provide a sufficient receiver deduplication boundary, or is a small runtime protocol/persistence extension required?
- Which runtime capability negotiation and build-provenance fields are needed across the two platform builds?

These remain evidence questions, not reasons to reconsider the selected shared-fork architecture.

## Documentation checkpoint

The package consists of `SKILL.md`, `agents/openai.yaml`, this plan, `runtime-investigation.md`, and the conditional `upstream-maintenance.md` design reference. It is ordinary canonical skill source, so it can be versioned and transferred with the skill repository rather than depending on an ignored task report.

Both structural validators exited successfully on `2026-10-02`. On `2026-10-03`, `skills-ref validate ./codex-peer-collaboration` and `skills-ref validate ./upgrade-codex-patch` exited `0` after the release patch was retained and this checkpoint was added. The canonical pull was already up to date; existing documentation/workflow commits `a7c4505` and `feaf409` are preserved. The current `$manage-agentic-skills-repo` contract owns the complete repository commit, and the invoked upgrade workflow requires publication. Runtime activation and harness synchronization keep their separate authority. Structural validity does not establish correct activation or end-to-end peer behavior.
