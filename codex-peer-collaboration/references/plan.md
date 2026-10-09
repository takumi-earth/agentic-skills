# Codex peer collaboration: living plan

Last materially updated: `2026-10-09`, `Asia/Hong_Kong`.

This is the maintained project record requested by the user, outside the Codex checkout. Keep this file current rather than creating parallel plans. [Runtime investigation](runtime-investigation.md) owns the detailed source findings.

## User-selected objective and decisions

The user wants existing independent sessions they directly interact with and monitor to support discovery, messages, replies, and bounded delegation through the shared runtime. The user identifies which agents may interact and for what purpose. Necessary exchanges within that explicit scope can proceed without repeated permission; apparent relevance or speculative overlap does not authorize contacting another agent or expanding the purpose.

The required client and host combinations are:

1. Ubuntu sessions collaborating while the user operates them through the Mac desktop app.
2. Mac sessions and Ubuntu sessions collaborating with each other while the user monitors both through the desktop app.
3. The same collaboration while the user connects through the ChatGPT phone app to the desktop app. The user reports that phone access to sessions on both hosts already works.
4. Continued use of the source-built Codex CLI/TUI on both Mac and Ubuntu.
5. Minimize recurring effort to pull upstream changes and carry the peer feature forward, while preserving the selected architecture and correctness.

The selected architecture is one enhanced Codex fork, built for each platform, with peer collaboration owned by the app-server runtime. Each host has its own runtime, session state, and filesystem. Desktop and TUI clients attach to the appropriate runtime; the two runtimes exchange peer messages through an authenticated connection.

Authority provenance is the actual user statements in session `01a0f6cc-3471-74bd-ac52-cf42b069b52a`:

- The user distinguished existing independent peers from subagents and later clarified that the user grants the recipient and purpose for communication or delegation. Sharing a plan permits delivery and acknowledgment of awareness; it does not assign implementation or oversight. Subagent delegation requires explicit requests.
- The user requested a shared enhanced Codex repo and its app-server in both locations, with the desktop app using their own primary runtime.
- The user stated that the desktop app has no such UI configuration and explicitly directed source investigation.
- The user requested durable documentation outside the Codex repo, then explicitly requested a new skill with the plan in its references.
- The user requested an approach with the minimum practical overhead for updating upstream Codex and reapplying the changes.
- On `2026-10-09`, the user requested notifying the existing `codex-bun` peer about this skill and plan and preserving all five maintenance enhancements described below. The user confirmed that this peer already has reusable patching infrastructure without patch files. The user explicitly clarified the original communication scope: share the plan and establish awareness; whether and when the recipient integrates it belongs to that session and its user. Earlier assistant-authored incorporation assignments and API handoff expectations exceeded that request and are not authoritative.

These decisions are protected project requirements. Reopen them only when the user changes the requirement or a concrete incompatibility needs their decision. Assistant proposals and status do not create new authority.

## Scope and boundaries

- Peer communication covers only the user-designated recipient and authorized purpose. An existing child is not a peer. Ask the user before contacting another agent or expanding the purpose; speculative overlap is never sufficient.
- Spawning, creating, or forking sessions and delegating to subagents require explicit user requests.
- Peer delegation requires an explicitly authorized recipient and bounded assignment. A plan-sharing request permits delivery and acknowledgment of awareness, not implementation assignments, progress/API requests, integration obligations, or follow-on scheduling. Do not inspect another session's objectives, repository, paths, or status to invent communication scope or manage its priorities.
- Peer messages carry authenticated sender provenance and remain tool-originated context rather than human instructions.
- Apply the user's explicit communication scope through the configured peer approval policy. The selected TUI peer-send policy is `"approve"`; that runtime setting does not grant conversational authority, delegation, or approval for creating/forking sessions or unrelated actions. The recorded global policy remains `approval_policy = "on-request"` with `approvals_reviewer = "user"`. Do not ask again for exchanges already covered by the user's named recipient and purpose.
- Source changes, builds, verification, installation, service restarts, runtime activation, staging, commits, and pushes follow the authority for the current phase. This document does not authorize them.
- Earlier suggestions for a separately configured peer MCP service were planning alternatives. The user subsequently selected runtime ownership in the shared Codex fork; do not silently restore the earlier architecture.

## Working roots and baseline

| Item | Recorded value |
| --- | --- |
| Authoritative Ubuntu Codex source | `~/rust-forks/codex-orig`; Rust workspace `codex-rs/` |
| Source checkpoint inspected | `rust-v0.159.2`, Git `HEAD` `ff6aec96948b70d94983af2641a6b67c94faeff5`, with the user's existing patch and peer-approval edits |
| Current release-upgrade run | `rust-v0.162.0`, Git `HEAD` `c1382380de69521303b416720a52f42d51af6248`; all Cargo installs, patch audit, complete installation, and native daemon version checks pass; exact patch resource retained for publication |
| Latest installed release upgrade | `rust-v0.162.0`; CLI, selected daemon, and running app-server verified at `0.162.0`, with native local pin and a successful complete-installation receipt |
| Previous completed release upgrade | `rust-v0.161.0`, Git `HEAD` `979011409de0a60b52f179721948e65531d26144`; complete Ubuntu package installed and source daemon selected, pinned, and verified at that checkpoint |
| Canonical skill source | `~/agentic-skills/codex-peer-collaboration` |
| Mac source checkout and active local backend | Not yet established by on-host evidence |
| Conversation provenance | `01a0f6cc-3471-74bd-ac52-cf42b069b52a` |

The similarly named checkout `~/rust-forks/codex/codex-rs/bun` belongs to separate Codex-Bun work. It was not the authoritative source for this installation.

## Current requirement state

| Requirement or lane | State and evidence |
| --- | --- |
| User-scoped peer permission and subagent distinction | `~/.codex/AGENTS.md` hardened on `2026-10-09`: the user grants recipient and purpose; plan sharing permits delivery and acknowledgment, not implementation delegation, speculative contact, or oversight of another session |
| TUI peer-message approval setting | Carried, compiled, and installed for `0.162.0`; selected and running Ubuntu daemon verified at the same version, preserving upstream worktree-tool support and approval behavior. Exact patch resource retained; Rust tests were not executed under the upgrade contract |
| TUI bridge after daemon recovery | Absent from the earlier automatic recovery-turn inventory; advertised again in normal TUI turns, with successful peer discovery on `2026-10-08`. The current harness exposes native `codex_tui` list/read/send/wait tools, and list/read/send succeeded for the `codex-bun` coordination on `2026-10-09`. This bridge evidence does not implement app-server-owned peer tools; exact per-restart reconnect ordering remains unverified |
| Shared-runtime local peer tools | Not implemented; current `collaboration` tools expose only the current agent tree |
| Package selection and pinning | Confirmed in source; complete local packages can be selected with `update --from-cli` |
| Ubuntu runtime selection and client boundary | The initial `2026-10-09` installation rejects a responsive unmanaged `0.161.0` app-server. After the user's shutdown and successful TUI `/daemon` package update, a detached supported installation completes and verifies CLI/selected/running `0.162.0`. Normal TUI startup uses the native lifecycle owner; direct shared-socket server launches bypass PID registration. The actual launcher responsible for the earlier instance and the full desktop/Mac/phone acceptance matrix remain unverified |
| Mac desktop attachment to our selected runtime | Unverified; no UI selector is available or required as an investigation prerequisite |
| Mac-Ubuntu peer routing | Not implemented |
| Phone use of native peer tools | Not verified; current phone access to both hosts is user-reported existing behavior |
| Durable skill and plan | Created in canonical source; the Codex skill projection resolves there; prior structural validation and Ubuntu synchronization are recorded, with release retention and publication owned by the current upgrade workflow |
| Low-overhead upstream maintenance | All five requirements in `upstream-maintenance.md` selected by the user on `2026-10-09`; semantic peer declarations, reproducible release generation, and the package reuse lane remain unimplemented |
| Codex-Bun plan awareness | Published skill/plan `392e662f5951a1063691bef5a331a8130725a1f6` delivered to peer `01a0f378-ec34-7657-ac19-f22a04282c55`; its response establishes awareness. The user will plan directly with that session after its current priorities. Earlier incorporation/API assignments were assistant overreach and are withdrawn as requirements; the recipient decides whether and when to integrate the plan |

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

The user invoked `$upgrade-codex-patch` on `2026-10-09` for the clean selected `rust-v0.162.0` checkout. Source/build/artifact preparation, complete Ubuntu installation, and native runtime activation now succeed. The audited patch is retained in the skill package for the upgrade's mandatory publication. This run does not implement native peer collaboration.

- Target base: `c1382380de69521303b416720a52f42d51af6248` in `~/rust-forks/codex-orig`; baseline worktree and index were clean. The canonical skill refresh was already up to date.
- Selected predecessor: `~/agentic-skills/upgrade-codex-patch/assets/patches/codex-v0.161.0.patch`, SHA-256 `48566d8c7e8724f63f4d4f7569512cd2fe793ce3c0cc3665935944aa49a40d94`; `118154` bytes, `2896` lines, `47` paths, `179` hunks. Predecessor bytes remain unchanged.
- Rebase: account for six rejected hunks across four complete owner files. Preserve the new workspace fields, TUI `ToolServices` argument, invalid-worktree lifecycle scenario, and `create_worktree` approval configuration. Comparison reports `46` identical file edit streams and one upstream-aware lifecycle-test adaptation, with no removed or added file sections.
- Audited local successor: `~/rust-forks/codex-v0.162.0.patch`, retained byte-identically at `~/agentic-skills/upgrade-codex-patch/assets/patches/codex-v0.162.0.patch`, SHA-256 `ed1c958b57d0d340dbc2cba94eb67916ac8039b876a368aa5d99c8208000f080`; `118488` bytes, `2898` lines, `47` paths, `180` hunks. Cached and private-target-base applicability both pass, as do exact reviewed-export equality and predecessor/base/staged-entry preservation. The source and selection remain unchanged through the runtime handoff and successful retry, so the existing audit remains applicable.
- Preparation and Cargo: `just i --prepare-v8` exits `0` in `0.943` seconds; `cargo upgrade --recursive --verbose` exits `0` in `39.214` seconds; `cargo update --recursive` exits `0` in `4.083` seconds; `cargo install --path cli` exits `0` in `1194.848` seconds and installs `codex` plus `logs_client`; `cargo install --path code-mode-host` exits `0` in `135.452` seconds and installs `codex-code-mode-host`. No build remediation or new pins were needed. Retain the carried workspace pins for `blake3`, `time`, and `zune-core`, and `cc = "=1.2.55"` in `utils/rustls-provider/Cargo.toml`; the audit records inherited and upstream pins through their actual manifest owners.
- Complete installation attempt: an independent `just i` process reuses all three prebuilt binaries, builds/validates the official Linux package with source-built `bwrap`, verifies `0.162.0`, and publishes CLI aliases. It exits `1` in `10.502` seconds at native `update --from-cli --yes`: `app server is running but is not managed by codex app-server daemon`. No daemon replacement occurs and the final installation receipt is not updated by this failed invocation.
- Initial retained CLI package: `~/.codex/packages/standalone/releases/local-0.162.0-x86_64-unknown-linux-gnu-503638ca-4e80-4206-9b94-7801f78fd6e5`. At the first failed attempt, the native start response reports CLI `0.162.0`, selected daemon `0.161.0`, and running app-server `0.161.0`; the responding socket belongs to PID `14117`, running a source-built `0.161.0` standalone package, with current and legacy PID records absent. These remain historical checkpoint facts, not a durable PID selection rule.
- User-performed handoff: the user reports `pkill codex` and supplies a plain `just i` log. Its builds and CLI publication succeed in about `1169` seconds, retaining package `~/.codex/packages/standalone/releases/local-0.162.0-x86_64-unknown-linux-gnu-8f8a1730-94f4-4a9b-909e-381cd1dfe9e9`, before the same native ownership rejection. The user identifies the earlier instance as originating from the `0.161.0` upgrade. In the resumed TUI, live evidence shows a new managed `0.161.0` daemon with a valid PID record; the user's `/daemon` action then selects, pins, and runs `0.162.0`. This resolves the earlier unmanaged-process approval boundary without the agent killing that instance. It does not establish whether a process survived `pkill` or which launcher created the instance at the failed installation.
- Complete supported retry: `just i` reuses all three prebuilt binaries in an independent recorded process, exits `0` in `76.691` seconds, and writes `~/.codex/packages/standalone/source-install.json` with `version = "0.162.0"`, `status = "installed"`, and `daemon = "selected-and-verified"`. Current CLI package: `~/.codex/packages/standalone/releases/local-0.162.0-x86_64-unknown-linux-gnu-5d49ca2d-4a85-49f0-9b85-d1ce9c75096e`. Native readback confirms CLI/selected/running `0.162.0`. The native owner requests graceful shutdown, uses its configured force deadline, publishes the replacement PID record, and verifies readiness; recovery checks the original invocation rather than repeating installation.
- Startup alignment investigation: installation publishes the standalone CLI and separately updates the daemon selection. Normal TUI startup calls the native owner and preserves an existing daemon package; a direct `app-server --listen unix://` launch bypasses that owner's PID publication. A first `SIGTERM` requests draining active turns rather than proving process exit. The native PID backend does not register a reboot-persistent service; no Codex system or user `systemd` unit was found on this host. The exact external/desktop startup path remains an evidence question. [Runtime investigation](runtime-investigation.md#installation-startup-and-ownership-follow-up) records the source chain and limits.
- Authority boundary: preserve native ownership checks, shared feature settings, and the user's communication scope. No unmanaged server was killed by the agent, no ownership record was forged, no Cargo install was repeated, and no upgrade notice was sent to another agent during recovery. Native package selection and its managed restart remain effects already authorized by this upgrade.
- Command fallout and evidence: Cargo refreshes ordinary versions in `19` manifests and the lockfile; `17` additional manifest paths are recorded as mutation bounds while those versions and `Cargo.lock` remain excluded from the `47`-path selected artifact. Both Cargo installs and the complete-package attempt change no checkout source after resolution. Rust tests, formatting, linting, and generators were outside this upgrade contract. Diagnostics are the configured stable-toolchain notice and the host-only unused `crossterm` patch; the CLI graph uses that patch.
- Intrinsic evidence: `~/agentic-skills/.scratchpad/upgrade-codex-patch/20261009T053728Z-v0.162.0/` contains immutable baseline/phase snapshots, the curated selection, command streams/status/durations, failed and successful installation receipts and launch records, final comparison, and passing patch audit. The handoff and successful installation change no tracked or untracked Codex source paths; base, staged entries, and predecessor bytes remain unchanged.

## 0.161.0 completed release upgrade checkpoint

The user invoked `$upgrade-codex-patch $codex-peer-collaboration` on `2026-10-07` for the clean selected `rust-v0.161.0` checkout. This invocation carries the existing peer-approval behavior; native runtime peer tools, cross-host routing, and the client acceptance matrix remain unfinished.

- Target base: `979011409de0a60b52f179721948e65531d26144` in `~/rust-forks/codex-orig`.
- Selected predecessor: `~/agentic-skills/upgrade-codex-patch/assets/patches/codex-v0.160.0.patch`, SHA-256 `46f0d483ee4371ca91b3f3341daeb200a97501602bcd514b6404c02ac340c358`; `119515` bytes, `2921` lines, `49` paths, `182` hunks. Its digest matches the exact packaged patch selected by the user in session `01a1006c-be1f-72f1-833b-1c31b63934d4`. The older local `0.160.0` copy is preserved and was not substituted.
- Rebase: classify six failed owner files, apply once with rejects, and port every unapplied intent. Upstream already supplies the `chatgpt` recursion limit and the unused registry import removal. Preserve the new TUI `Features` argument, bootstrap preference loading, and `Box::pin` handling. Remove only the generated rejects after accounting for them.
- Successor: `~/rust-forks/codex-v0.161.0.patch`, retained byte-identically at `~/agentic-skills/upgrade-codex-patch/assets/patches/codex-v0.161.0.patch`. SHA-256 `48566d8c7e8724f63f4d4f7569512cd2fe793ce3c0cc3665935944aa49a40d94`; `118154` bytes, `2896` lines, `47` paths, `179` hunks.
- Curated selection and comparison: `45` file edit streams and `177` hunk edit streams identical to the predecessor. Exclude the predecessor's ordinary `bitflags` bump, all automatic Cargo version refreshes, and `Cargo.lock`. Keep the private field/hunk selection separate from the live build inputs. The lifecycle test adaptation and two fixes already present upstream account for the remaining carried differences.
- Preparation and Cargo: `just i --prepare-v8` exits `0` in `0.387` seconds; `cargo upgrade --recursive --verbose` exits `0` in `40.390` seconds; `cargo update --recursive` exits `0` in `5.064` seconds; `cargo install --path cli` exits `0` in `1142.940` seconds and installs `codex` plus `logs_client`; `cargo install --path code-mode-host` exits `0` in `118.699` seconds. No build remediation or new pins were needed. Retain workspace pins `blake3 = "=1.8.2"`, `time = "=0.3.47"`, `zune-core = "=0.5.1"`, and the `cc = "=1.2.55"` build dependency in `utils/rustls-provider/Cargo.toml`.
- Complete installation: `just i` reuses all three prebuilt binaries, validates the official Linux package with source-built `bwrap`, publishes CLI aliases, and selects the native source daemon. Two daemon restarts interrupted installer processes owned by the old command session. A third invocation in an independent process completed with exit `0` in `74.110` seconds and wrote the final receipt; the Rust installations were not repeated.
- Runtime provenance: complete CLI package `~/.codex/packages/standalone/releases/local-0.161.0-x86_64-unknown-linux-gnu-34f4a207-b3bd-4353-952a-45eff0350963`; selected daemon package `~/.codex/packages/app-server-daemon/releases/local-421231a21cd28fd56163bcf9b38327f1a2f9d538db0162aed3c79d1953affe0b-x86_64-unknown-linux-gnu`. CLI, managed daemon, and running app-server versions are all `0.161.0`. The running app-server and Code Mode host executable hashes match the installed CLI package's respective binaries. The daemon's production-update marker is absent, preserving the native local pin. This is runtime/package evidence, not acceptance of native peer tools or the complete client matrix.
- Tool visibility at the upgrade checkpoint: the automatic recovery turns omitted `codex_tui` list/read/send/wait tools, while `collaboration.list_agents` exposed only the current root. This was a turn-scoped observation, not a permanent capability-loss verdict. Normal TUI turns later advertised the tools again and peer discovery succeeded; the follow-up below owns the updated findings. No listener or client-configuration workaround was applied.
- Audit and worktree: cached applicability and applicability against a private filesystem view of the target base both pass. The original-baseline audit fails only the physical index check; the final audit passes against the separately recorded user-accepted exception. Predecessor bytes, `HEAD`, staged entries, and exact reviewed-export bytes are preserved. The `64` modified Codex paths remain unstaged and uncommitted; automatic version fields and `Cargo.lock` are excluded from the `47`-path artifact. The audit records the `16` additional manifest paths touched by Cargo as mutation bounds, not selected export content.
- Index exception: `HEAD` and staged entries remain identical to the original baseline, but the physical index digest changed between the baseline and post-application snapshots. The user explicitly accepted: `Accept the metadata exception; preserve the unchanged staged entries`. Preserve the original baseline and record this run's exception separately; no index restoration or rewrite is authorized.
- Diagnostics and evidence boundaries: the CLI retains a future compatibility warning from `proc-macro-error2 v2.0.1` re-exporting private `proc_macro`; the host-only graph reports the unused workspace `crossterm` patch, which the CLI uses. Both installers report the configured stable-toolchain notice. Source inspection, artifact checks, compilation, installation, and runtime provenance are verified separately; Rust tests, linting, formatting, generators, and end-to-end peer/client checks were not run under this upgrade contract.
- Intrinsic evidence: `~/agentic-skills/.scratchpad/upgrade-codex-patch/20261007T115114Z-v0.161.0-peer/`.

The retained patch and this checkpoint follow the invoked upgrade's complete canonical repository commit and publication workflow. The next unfinished project actions remain native local peer implementation and Mac attachment investigation; preserve the selected runtime ownership and acceptance matrix below.

## Recovery and guidance follow-up

On `2026-10-08`, the user supplied the daemon feature-mismatch screen and reported completing its restart. The selected source confirms an upstream `api_key_model_discovery` default change from `false` in `0.160.0` to `true` in `0.161.0`. Ubuntu readback confirmed the running source version and saved overrides, and `codex_tui.list_threads` worked again. [Runtime investigation](runtime-investigation.md#recovery-and-feature-compatibility-follow-up) records the source mechanism and its evidence limits.

Keep native package replacement, shared feature-policy changes, and client MCP reattachment distinct. The authorized upgrade's default installation already owns native daemon selection/restart; the TUI compatibility action changes all displayed persisted feature values under the user's separate selection. A screenshot does not authorize either effect on another host. The installation invocation and recorder must survive the daemon being replaced, and recovery must check the original invocation/receipt before repeating completed commands.

The earlier raw-index exception is historical run evidence. The refreshed upgrade contract protects staged entries and the staging split while permitting normal Git index-cache refreshes. Its current helper does not use serialized index bytes as an acceptance criterion. Do not reintroduce the obsolete byte check, restore index bytes, or request another metadata exception from this checkpoint.

The temporary inventory gap and later successful TUI discovery do not satisfy the native runtime or desktop/Mac/phone acceptance requirements. Native peer lifetime/registration and Mac attachment remain unfinished; exact reconnect ordering for the upgrade interruptions is still an evidence question.

## Previous release upgrade checkpoint

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

## Selected upstream maintenance requirements

The user's `2026-10-09` request selects these requirements. [Upstream maintenance](upstream-maintenance.md) owns their detailed contract; this selection does not claim that the updater or runtime capability is implemented.

1. Keep the registry, message protocol, delivery state, authenticated cross-host connection, and peer policy together in a focused app-server-owned runtime component. Connect it through actual workspace/build, runtime construction/lifetime, tool registration, and configuration/protocol owners. Record verified integration points and their change frequency; candidate families and line counts do not establish maintenance cost.
2. Locate and apply integration points by their types and relationships across complete permitted scopes. Preserve formatting-independent and location-independent discovery, unrelated behavior, exact contribution cardinality, recognized pre-state and post-state, validated outcomes, and replay without further changes. Ambiguous or incompatible targets and failed validation leave authoritative source unchanged and identify the affected integration point.
3. Inspect and reuse the existing Codex-Bun integration machinery before introducing another engine, within a separately authorized implementation phase. Use bounded capability crates, virtual-source transactions, semantic indexing, explicit edit ownership, and replay where they satisfy the peer declarations. Keep upgrade tooling outside the shipped peer runtime's dependency graph; broader Bun dependency/runtime changes retain their own workflow scope. Sharing this requirement with the peer does not assign its implementation.
4. Generate reproducible versioned patches as release and audit artifacts from owned peer code plus semantic integration declarations for each accepted upstream base. Peer source application uses reusable declarations rather than patch-file input. Preserve the causal sequence: resolve upstream revision, prepare target, restore owned code, apply and validate integration points, run the authorized build sequence, assemble platform packages, audit and retain artifacts, and activate within the applicable authority. Compatible interfaces should require zero manual porting; actual API or ownership drift requires a bounded repair.
5. Build once per platform and accepted build revision, preserve normal caches, and assemble/install packages from the successful binaries. Account for rebuilds caused by upstream workspace, dependency, and toolchain changes. Keep local compilation supported; a later CI build/distribution lane remains separate proposed work.

## Codex-Bun peer notification scope

The user designated existing independent peer `codex-bun`, session `01a0f378-ec34-7657-ac19-f22a04282c55`, to receive this skill and plan. The authorized exchange is delivery and acknowledgment that the recipient is aware of it. The published skill/plan was delivered through native messaging, and the peer's response establishes awareness. No implementation, incorporation, API handoff, progress report, or follow-on obligation is assigned by this notification.

On `2026-10-09`, the user clarified that earlier assistant-authored incorporation assignments, inspection of the peer's priorities, and API handoff expectations exceeded the original request. Those expectations are withdrawn as requirements. This is a correction of the assistant's interpretation, not a new consumer objective or a request to investigate the recipient's work. The user also required retraction of an unrelated release-upgrade notice; the retraction was delivered.

The user will interact directly with `codex-bun` to plan next steps once its current priorities are completed. Whether and when that session integrates this capability belongs to the recipient and its user. Preserve all five maintenance requirements as project design without making them assignments to the peer. Do not monitor its priorities, schedule an automatic follow-on, or send further notices outside the user-authorized plan-sharing scope.

Future implementation under its own authorization should retain the shared app-server architecture and assess reusable machinery through actual owners. Source integration, compilation, executed behavior, platform packages, activation, and desktop/Mac/Ubuntu/phone acceptance remain distinct evidence states. This notification does not establish those implementation outcomes.

## Next unfinished work

Mac attachment investigation and the native peer boundary/local implementation can progress independently within the current phase's authority. Do not make a missing Mac probe or UI control a prerequisite for source work that does not depend on it.

Design the peer boundary using [the upstream maintenance strategy](upstream-maintenance.md): keep substantive behavior in owned code, maintain a small inventory of upstream integration points, and evaluate semantic reapplication before creating another patch engine. Minimal maintenance effort cannot justify moving the feature out of runtime ownership or weakening delivery and authorization behavior.

1. **Establish Mac attachment through source-defined runtime interfaces.** Trace or observe which executable, package, socket, and transport the Mac desktop app actually uses. Exercise the selected managed-daemon/package path with proportionate authority. Verify whether desktop startup reuses it or creates a separate backend. Use process/socket evidence, not a requested UI selector or an invented config key.
2. **Plan the native local peer boundary and reusable integration.** The boundary should use a focused runtime component and thin integration with the session registry and tool pipeline, keep peer operations separate from child control, and define eligible-session discovery, bounded reads/waits, sender attribution, user-scoped approval policy, delivery receipts, and duplicate handling. The user will separately plan with `codex-bun` after its current priorities; that session decides its own integration scope and timing. This project step does not assign work to that peer.
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
- Exercise the selected semantic declarations against formatting, line shifts, unrelated extension, movement, recognized post-state, replay, ambiguity, and incompatible upstream ownership/API changes. Prove exactly-once integration and unchanged authoritative source on rejected application; patch-text matching or compilation alone does not establish these properties.
- Establish reproducible release-artifact generation and package reuse per accepted platform/build revision without making patch files the production application mechanism.

## Open questions

- Does the Mac desktop app use the standard control socket/managed daemon for local sessions, or a separately launched primary-runtime backend?
- Which package/connection integration point lets the app use our build durably without relying on a nonexistent UI selector?
- Does the existing tool-output API provide a sufficient receiver deduplication boundary, or is a small runtime protocol/persistence extension required?
- Which runtime capability negotiation and build-provenance fields are needed across the two platform builds?

These remain evidence questions, not reasons to reconsider the selected shared-fork architecture.

## Documentation checkpoint

The package consists of `SKILL.md`, `agents/openai.yaml`, this plan, `runtime-investigation.md`, and the conditional `upstream-maintenance.md` design reference. It is ordinary canonical skill source, so it can be versioned and transferred with the skill repository rather than depending on an ignored task report.

Both structural validators exited successfully on `2026-10-02`. On `2026-10-03`, `skills-ref validate ./codex-peer-collaboration` and `skills-ref validate ./upgrade-codex-patch` exited `0` after the release patch was retained and this checkpoint was added. The canonical pull was already up to date at that checkpoint; existing documentation/workflow commits `a7c4505` and `feaf409` are preserved. The current `$manage-agentic-skills-repo` contract owns the complete repository commit and publication; the invoked release-upgrade workflow retains its separate artifact obligations. Runtime activation and harness synchronization keep their separate authority. Structural validity does not establish correct activation or end-to-end peer behavior.

On `2026-10-09`, the user selected all five maintenance requirements and authorized notifying the named peer about the skill and plan. The user clarified that the notification permits delivery and awareness acknowledgment; it does not assign implementation or oversight. The earlier checkpoint's canonical refresh and both package validators succeeded. The Codex, Claude, and Copilot links expose this same canonical source. These are documentation/package facts, separate from runtime/client implementation evidence.
