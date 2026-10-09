# Runtime investigation evidence

Source checkpoint: `2026-10-02`, `Asia/Hong_Kong`; `~/rust-forks/codex-orig` at `ff6aec96948b70d94983af2641a6b67c94faeff5`, workspace `0.159.2`, with existing local patches.

This reference preserves findings already established by source inspection. [The living plan](plan.md) owns user decisions, current status, and next work. Refresh a finding when its owner or relevant external state changes; a source locator or checksum does not replace a required owner-file read after context loss.

Paths below are relative to `~/rust-forks/codex-orig/codex-rs`, except the package-builder paths explicitly rooted at the repository root.

## Package selection and pinning

| Semantic owner | Established behavior |
| --- | --- |
| `app-server-daemon/src/prepare_install.rs`, `update_from_cli` | Selects the invoking CLI's complete recognized package. This is the implementation behind `codex app-server daemon update --from-cli`. |
| Same file, `prepare_from_package` | Validates platform, metadata, complete contents, and executable identity; stages a copy; checks that source/selection did not change; stops the prior managed backend when replacing it; atomically selects the prepared release. |
| Same file, local-release naming and marker publication | Explicit replacement uses `local-{digest}-{target}` and removes the `auto-update-version` marker, pinning the local package instead of following public stable updates. |
| Same file, `validate_package` | Requires `codex-package.json`, the entrypoint, matching `codex-code-mode-host`, `codex-path/rg`, and platform-specific helpers. A bare Cargo-installed executable is insufficient for this installation path. |
| `app-server-daemon/src/managed_install.rs`, `package_root` and `managed_codex_bin` | Resolves the dedicated daemon package and preserves recognized legacy selection. The ordinary dedicated executable is `~/.codex/packages/app-server-daemon/current/bin/codex`. |
| `app-server-daemon/src/lib.rs`, `ensure_managed_updater` | Public-update eligibility depends on the selected stable release and marker; a pinned local selection does not become a public-update selection merely because its version resembles a release. |

Do not confuse explicit `--from-cli` selection with a fresh `daemon start`. Initial package preparation has different latest-channel rules. Observe the selected package and updater eligibility rather than inferring pinning from a version number.

## Daemon discovery and transport

| Semantic owner | Established behavior |
| --- | --- |
| `app-server-daemon/src/lib.rs`, `Daemon::from_environment` | Resolves `CODEX_HOME`, the standard control socket, lifecycle state, and the selected managed executable. |
| Same file, `Daemon::start` | Probes the control socket first. A reachable server is reused; this does not by itself prove managed ownership or selected-package identity. |
| Same file, restart/stop/replacement paths | Refuses managed lifecycle control when a reachable server is not owned by the daemon manager. This explains the earlier unmanaged-server errors. |
| `app-server-daemon/src/backend/pid_start.rs` | Resolves the selected binary before launch, launches it detached, and records process/executable identity. |
| `app-server-transport/src/transport/mod.rs`, `app_server_control_socket_path` | Derives the logical rendezvous `~/.codex/app-server-control/app-server-control.sock` from the host's `CODEX_HOME`. |
| `app-server-transport/src/transport/unix_socket.rs` | Implements guarded Unix-socket publication and WebSocket acceptance. Refuses replacing a live socket; the rendezvous can alias a protected physical socket. |
| `cli/src/main.rs`, `AppServerSubcommand::Proxy`; `stdio-to-uds/src/lib.rs` | `codex app-server proxy` relays raw bytes between stdio and the selected/default Unix socket. It is not a JSONL-to-WebSocket protocol converter. |
| `app-server/src/main.rs` and CLI app-server dispatch | Entrypoints accept stdio, Unix socket, WebSocket, or no local listener, and configure the Code Mode host and remote-control startup separately. |

## Package assembly and helper resolution

- Repository-root `scripts/codex_package/README.md` and `scripts/codex_package/layout.py` define the canonical package directory: `codex-package.json`, `bin/`, `codex-resources/`, and `codex-path/`.
- The builder supports `codex` and `codex-app-server` package variants and platform-specific artifacts. Package assembly supports prebuilt entrypoint/helper inputs.
- `install-context/src/lib.rs`, `CodexPackageLayout::from_exe`, recognizes canonical packages and a provisioned `CodexCLI.app/Contents/MacOS/codex` inside an outer package.
- `InstallContext::code_mode_host_program` first checks a packaged resource and then resolves the matching helper from the executable/package directory.
- `install-context/src/bundle_tests.rs` contains behavior evidence for recognizing the provisioned Mac CLI's outer package. Tests were read, not executed in this investigation.
- The canonical Codex package is proven source machinery. It is not evidence that every asset in the desktop's cached broader primary-runtime distribution is produced by this builder.

## Desktop launcher boundary

The complete `cli/src/app_cmd.rs`, `cli/src/desktop_app/mod.rs`, and `cli/src/desktop_app/mac.rs` were inspected.

`codex app` finds or installs the signed desktop app. `open_codex_app` validates the bundle and calls `open -a` with a `codex://threads/new?path=...` deep link. This code path does not pass a custom runtime directory or choose the desktop's internal backend.

The investigation has not located or established the Mac desktop client's internal local-backend selection/reuse policy in this checkout. This is not a claim that custom runtime integration is impossible or that all desktop components are unavailable in source. Continue tracing the actual launcher/connection boundary and validate it on the host. The absence of a UI setting is not a blocker for source investigation.

## Existing peer tools and authority

- `tui/src/dynamic_tools_mcp.rs` owns an ephemeral authenticated loopback MCP listener, its configuration, request connection, and lifetime. `Drop` aborts its server task.
- `tui/src/app_server_session.rs`, `start_dynamic_tool_mcp`, starts that transport for applicable external-daemon TUI sessions. Its injected `codex_tui` configuration is not a native desktop peer capability.
- `tui/src/dynamic_tools.rs` provides bounded list/read/wait operations and messaging through app-server APIs.
- Its `start_turn` uses `TurnStartParams.tool_output` with empty human input. `app-server/src/request_processors/turn_processor.rs` maps that into `ResponseItem::FunctionCallOutput`. Preserve this authority distinction.
- `core/src/tools/handlers/multi_agents_v2/list_agents.rs` lists through `session.services.agent_control` with caller/parent/session context. It is the current agent-tree surface, not the independent-peer registry.
- The native tool registration seam is in `core/src/tools/spec_plan.rs`, `registry.rs`, and `router.rs`. These were used for navigation/focused inspection; a complete native-peer integration design still requires reading the selected owners in full.

The live Ubuntu server accepted read-only diagnostic JSON-RPC over the shared socket: `initialize`, `thread/loaded/list`, `thread/list`, and `mcpServerStatus/list`. This established that independent sessions can be discovered without the TUI tool bridge. It did not deliver a peer message or test its approval behavior.

## Recorded live observations

These are dated evidence, not current-process invariants:

- Earlier, the shared server ran an unlinked `0.159.0` executable while installed clients were `0.159.2`. Replacing only `codex-code-mode-host` did not replace the parent or its loaded thread configuration.
- A `template-rs` thread retained endpoint `http://127.0.0.1:33553`, with no listener, while its relaunched TUI listened on `41413`.
- `app-server/src/request_processors/thread_processor.rs`, `resume_running_thread`, preserves loaded-thread configuration when another client can observe the thread or work is active; idle-cache replacement has narrower conditions.
- Later `0.159.2` runtime checks showed PID `14761`, executable `/xdg/cargo/bin/codex`, `--listen unix://`, and a `features.code_mode_host` override. The Code Mode host also used the installed executable.
- `codex app-server daemon version` reported CLI/app-server `0.159.2`, the standard socket, and `managedCodexVersion: null`. The process was serving the desktop connection, but this was not proof that a managed package had been installed or pinned.
- Inspected desktop threads had no attached `codex_tui` server. `collaboration.list_agents` returned only the current root; a direct app-server query found the independent active `template-rs-repair` session.

## Mac config supplied by the user

The supplied TOML was parsed successfully. This is syntax evidence, not validation of every key against the Mac's running binary.

- `tui.peer_message_approval_mode = "approve"` is present.
- `approval_policy = "on-request"` and `approvals_reviewer = "user"` are present.
- `features.multi_agent = true` and `agents.max_depth = 1` configure the child-agent surface; they do not establish independent-peer discovery.
- `mcp_servers.node_repl.env.CODEX_CLI_PATH` points to `/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex`. It is an MCP-child environment entry, not proof of the main desktop app-server selection.
- `marketplaces.openai-primary-runtime.source` points to `~/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime`, a plugin marketplace source.
- The supplied `[desktop]` preferences contain no runtime/executable-selection key. The user explicitly confirmed that no such UI control is exposed.

Do not invent a `desktop.primaryRuntimePath` key or change the MCP helper variable as a substitute for tracing backend selection.

## Primary documentation checked

- [App-server protocol](https://learn.chatgpt.com/docs/app-server): documents the JSON-RPC handshake, Unix/WebSocket transports, thread APIs, and tool-output turn delivery.
- [Remote connections](https://learn.chatgpt.com/docs/remote-connections): documents desktop-to-SSH-host setup and phone access using the connected host's tools and environment.
- [MCP integration](https://learn.chatgpt.com/docs/extend/mcp): documents shared host MCP configuration across desktop, CLI, and IDE clients. This supports an adapter option, but does not supersede the user's runtime-owned architecture.
- [Developer settings](https://learn.chatgpt.com/docs/developer-settings): documents `chatgpt.cliExecutable` for the IDE extension, not a desktop TOML runtime selector.

The documentation and source checks did not establish a supported desktop custom-primary-runtime selector. Managed daemon selection is confirmed; actual Mac desktop attachment is still the concrete handoff to verify.

## Recovery and feature compatibility follow-up

Checkpoint: `2026-10-08`, `Asia/Hong_Kong`; selected Ubuntu source at `rust-v0.161.0`, base `979011409de0a60b52f179721948e65531d26144`.

- Upstream changes `Feature::ApiKeyModelDiscovery` from default `false` in `0.160.0` to default `true` in `0.161.0` (`features/src/lib.rs`). `tui/src/daemon_startup.rs`, `compatibility_warning`, compares four client-required shared feature values with the daemon's threadless feature readback. A missing advertised feature is treated as disabled. The first mismatch determines the notice; the restart proposal contains all four client values.
- `tui/src/daemon_recovery.rs` requires an explicit selection/confirmation for the managed `Restart with these settings` action. `app-server-daemon/src/launch.rs`, `restart_with_features`, persists the selected overrides through the native lifecycle owner. This compatibility action differs from the installation's native package replacement; matching versions alone do not establish matching startup feature settings.
- The user reported completing the compatibility restart. On Ubuntu, the daemon then reported CLI/managed/running versions `0.161.0`, and its saved overrides were `api_key_model_discovery = true`, `auth_elicitation = true`, `code_mode_host = true`, and `mcp_oauth_refresh_coordination = false`. Saved overrides are configuration evidence, not a separate readback of every startup-captured service. These values do not become a policy for another host.
- During the earlier automatic recovery turns, the available-tool inventory omitted `codex_tui` list/read/send/wait tools. In subsequent normal TUI turns, those tools were advertised again and `list_threads` executed successfully. Treat the earlier absence as a scoped historical observation; it does not prove permanent removal or listener failure.
- The source exposes a recovery gap: `app-server/src/message_processor.rs`, `restore_daemon_threads`, uses default `ThreadResumeParams` and default `ClientMcpExtensions`; `request_processors/daemon_continuation.rs` can immediately continue interrupted work. Normal TUI resume instead injects its MCP configuration in `tui/src/app_server_session/rollout_history.rs` through `ThreadToolTransport::configure_mcp`. The daemon restore call does not supply that TUI override. Exact client-reconnect/continuation ordering for the observed interruptions was not established from runtime logs.
- The source mechanism, temporary absence, and successful later discovery are distinct evidence. Do not convert them into a proved per-restart timeline or declare the native peer project complete. The selected app-server-owned peer registry/tool lifetime remains the target; this investigation does not select persistence of TUI listener credentials or a global MCP configuration workaround.

## Installation, startup, and ownership follow-up

Checkpoint: `2026-10-09`, `Asia/Hong_Kong`; `~/rust-forks/codex-orig` at `rust-v0.162.0`, base `c1382380de69521303b416720a52f42d51af6248`. The user requests explaining why complete source installation and startup after reboot can disagree. Treat the earlier `0.161.0` instance as originating from the previous upgrade, as the user identifies it; do not invent a launcher or assume `pkill` failed to deliver its signal.

The current daemon lifecycle, package selector, PID backend, detached launch, process identity, feature-aware launch, native probe, TUI startup orchestration and policy, and canonical source installer were read through EOF. CLI app-server dispatch and the server's shutdown state were inspected at their relevant call sites. The earlier source locators are not substituted for these reads.

| Owner | Verified causal behavior |
| --- | --- |
| Canonical `upgrade-codex-patch/scripts/install_codex.ts`, `installLinks` and `install` | Publish CLI aliases and `packages/standalone/current`; then separately invoke native `daemon start`, `update --from-cli --yes`, and version verification. Build/publication can succeed before daemon selection fails. No startup service is registered by this installer. |
| `app-server-daemon/src/managed_install.rs`, `package_root` and `managed_codex_bin` | Prefer the dedicated `packages/app-server-daemon/current` selection; preserve recognized legacy standalone launch state. An existing daemon selection is independent of the foreground CLI's version. |
| `app-server-daemon/src/lib.rs`, `Daemon::from_environment` and `current_installation` | Resolve the same control socket and choose dedicated `daemon.pid` or legacy `app-server.pid` according to the selected package root. Re-resolve selection after acquiring the lifecycle lock. |
| `tui/src/startup_orchestration.rs`, `run_main_inner`; daemon `launch.rs`, `start_with_features` | Normal eligible TUI auto-start enters the native lifecycle owner. An existing socket may be reused; the TUI retains whether the returned `backend` identifies managed ownership. Startup does not implicitly replace an existing daemon package with the invoking CLI's package. |
| Daemon `lib.rs`, `Daemon::start`; daemon `client.rs`, `probe` | `start` probes first and can return `alreadyRunning` with no `backend`. The probe completes a live WebSocket/JSON-RPC initialization and reads the server's version; a stale socket path alone cannot produce that version response. Reachability does not adopt the server into managed ownership. |
| Daemon `prepare_install.rs`, `prepare_from_package` | Explicit replacement requires a recognized running backend or an unresponsive control socket. A responsive server with no recognized backend triggers the exact unmanaged-server error. The guard is preserved across the inspected `0.161.0` to `0.162.0` lifecycle code. |
| `app-server-daemon/src/backend/pid_start.rs`, `start_inner` | Canonicalize the selected executable, reserve the PID file under a lock, launch detached with `setsid` on Unix, capture process/executable identity, and atomically publish the PID record. `--managed-daemon` is an optional server behavior flag; it does not itself register a directly launched process. |
| Backend `pid.rs` and `pid_identity.rs` | Recognize ownership through the recorded live process identity. Linux boot ID and start ticks distinguish stale records and reused PIDs after reboot. Missing records do not cause discovery and adoption of an arbitrary socket owner. |
| `cli/src/main.rs`, app-server dispatch | Direct `codex app-server --listen unix://` enters server runtime construction without the daemon manager's launch/registration operation. `app-server proxy` relays an existing socket and does not perform native startup. These are separate entry paths from `app-server daemon start`. |
| `app-server/src/lib.rs`, `shutdown_signal` and `ShutdownState` | A first `SIGTERM` begins graceful drain and waits for active turns and admitted requests. A second forceable signal requests forcing. Native managed stop also owns a grace deadline and force termination. `pkill codex` delivering its default signal does not establish that all matching processes have exited. |

The inspected Unix backend creates detached processes, not a reboot-persistent service. The native README also states that its updater loop is not reboot-persistent. Both system and user `systemd` unit inventories on this Ubuntu host had no Codex entries, and the inspected unit directories had no Codex definitions. This does not identify every possible external boot hook or the Mac desktop's SSH launcher.

At the failed installation, the native `start` response lacks `backend`, and replacement rejects ownership. Before the user's later `/daemon` action, live inspection instead identifies a `0.161.0` daemon started by the resumed `0.162.0` TUI, with a valid dedicated PID record. The user's native package update succeeds and reports selected/running `0.162.0`. A subsequent supported detached `just i` completes with exit `0` in `76.691` seconds and records the matching installation. These are different observed ownership states; the successful handoff does not prove the missing record's earlier cause.

Remaining source/client integration question: identify the actual startup path that produced the earlier responsive unregistered server, including the desktop/SSH boundary where applicable. Align shared-socket startup with the native lifecycle owner and selected package; preserve explicitly requested standalone/stdin/custom-listener behavior and shared feature policy. An early passive ownership check could report this condition before expensive compilation, but is only a proposed installer improvement. No launcher rewrite, new service, process adoption, or weakened ownership guard was implemented in this investigation.
