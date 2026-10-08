# Complete source-package installation

The package's `justfile` owns `just i`. Import it from the Codex checkout with:

```just
import? x'${AGENTIC_SKILLS_REPO:-~/agentic-skills}/upgrade-codex-patch/justfile'
```

Use Just `1.32` or newer and Bun `1.4.1` or newer. The recipe uses a Bun script interpreter and enables Just's required `unstable` setting in the imported justfile rather than requiring callers to supply a flag. It does not use the Codex checkout's Python shell adapter. The actual package build still uses Codex's supported Python `3.11+` package builder.

The installer probes that interpreter's native certificate paths. When its default CA bundle is missing, no `SSL_CERT_FILE` or `SSL_CERT_DIR` override is supplied, and the host is Unix, it selects an existing system CA bundle for its child processes. Certificate verification remains enabled. Existing Python defaults and explicit certificate overrides are preserved; Windows retains Python's native certificate-store behavior. The selected fallback is reported before package assembly and does not change global shell or interpreter settings.

## Location authority

| Location | Selection |
| --- | --- |
| Skill resources | The imported justfile's `source_directory()`; `AGENTIC_SKILLS_REPO` selects the import, with `~/agentic-skills` as its default |
| Codex checkout | `CODEX_REPO_ROOT`, already exported by the checkout's root justfile; required for direct skill invocation |
| V8 checkout | `CODEX_V8_REPO` when set; otherwise the checkout's configured Cargo wrapper path, then a sibling `codex-v8` |
| Runtime state | `CODEX_HOME`, with the CLI's usual `~/.codex` default |
| Installed CLI aliases | `CARGO_HOME/bin`, with `~/.cargo/bin` as the Cargo default |
| Python interpreter | `CODEX_INSTALL_PYTHON`, defaulting to `python3` on Unix and `python` on Windows |

Use absolute paths or `~/...` for explicitly supplied repository locations. An explicit invalid V8 location fails; it does not silently select another checkout. The installer passes the resolved native wrapper through `RUSTC_WRAPPER` to child builds without rewriting the checked-in Cargo configuration. It selects the Bun running the installer for helper processes, including when `CODEX_V8_BUN` chooses a different compatible executable.

```bash
export AGENTIC_SKILLS_REPO=~/work/agentic-skills
export CODEX_V8_REPO=~/work/codex-v8
just i --plan
just i
```

`--plan` reads the selected inputs and compiler host and prints their normalized JSON without installing, building the launcher, or starting services.

## Installation chain

`selected checkouts -> native V8 setup -> official platform package build and validation -> logs_client -> compiled CLI version check -> immutable local package -> recoverable CLI aliases -> native daemon selection/pinning -> version verification`.

The compiler's host triple selects the package ABI. Linux packages include the source-built `bwrap`; Windows packages include `codex-command-runner.exe` and `codex-windows-sandbox-setup.exe`. The supported builder supplies verified `rg` and the patched `zsh` where available. The installer retains `logs_client` in the package in addition to its required runtime executables.

The published package lives beneath `CODEX_HOME/packages/standalone/releases/local-<version>-<target>-<unique-id>`. Old packages remain available. Unix CLI aliases are symlinks into the complete package. Windows uses native Bun proxies so the actual Rust executable still runs inside its package and no file-symlink privilege is needed. Replaced aliases and update markers are retained as `.before-source-install-<unique-id>` backups.

A SQLite transaction serializes publication. Build or identity failures leave installed aliases untouched and clean only the installer's staging directory. An alias-publication failure restores its prior aliases. Once a package has been published, later failures retain it and report the observed installation state. The final receipt is outside the immutable package, at `CODEX_HOME/packages/standalone/source-install.json`.

By default, `just i` starts the managed app-server when necessary, then invokes `update --from-cli --yes` and verifies the CLI, selected daemon and running daemon versions. This can restart a managed daemon. The native daemon owner decides whether the existing server is managed; the installer never kills an unmanaged server or substitutes a production release for the source build.

This native package selection and its managed restart belong to the authorized default installation. A companion project skill does not require another permission request for the same effects. Editing guidance or building a package without installation authority keeps its separate boundary.

Use `just i --no-daemon` to install the complete CLI package without starting or selecting a daemon. Use `just i --prepare-v8` to build only the V8 launcher before the upgrade's Cargo sequence.

## Execution through the daemon being replaced

Before launching the default installation from an agent hosted by the target daemon, arrange an independent process lifetime and durable stdout, stderr, exit-status, and duration capture. Use an external terminal or a child process whose lifetime and stdio do not depend on that daemon's command session. Preserve the selected repository locations and the same supported `just i` arguments.

A daemon-recovery prompt records an interruption, not command success or failure. Check whether the original installer is still running, then inspect its captured exit and `source-install.json`. A daemon running the target release can coexist with an unfinished installer and an older receipt. Continue observing a live installer; retry only when the invocation ended without completing the required installation. Correct the process lifetime before that retry, reuse the successful prebuilt binaries, and report interrupted attempts separately. Do not repeat Cargo installs or another attached `just i` merely because a tool response was lost.

## Shared features and client recovery

Package/version verification does not prove that the daemon's startup feature settings match a TUI client's requirements. Distinguish release defaults, saved daemon overrides, and the running server's feature readback. For example, upstream `0.161.0` changes the default of `api_key_model_discovery` from `false` to `true`; a daemon retaining the earlier effective value can trigger the TUI compatibility dialog without a failed package installation.

Preserve configured feature policy. Native package replacement does not itself authorize rewriting shared feature overrides to match a diagnostic. The TUI's `Restart with these settings` action applies all displayed shared values and persists them for other clients; use the user's actual selection or existing authorization for those specific changes. A screenshot is evidence, not a restart instruction. Do not generalize one host's accepted values to another.

After a restart, report the recovered turn's tool inventory separately from subsequent normal client turns. Temporary absence of `codex_tui` tools does not establish permanent removal, a dead listener, or a confirmed cause. Verify the current client handoff when needed, retaining source findings and timing inferences as separate evidence. Peer/client acceptance remains its project's own requirement; it is not an extra Cargo gate for this upgrade.

## Reuse successful upgrade builds

After both Cargo installs have succeeded, pass all three existing binaries to avoid rebuilding them:

```bash
codex_cargo_bin="${CARGO_HOME:-$HOME/.cargo}/bin"
just i --entrypoint-bin "$codex_cargo_bin/codex" --code-mode-host-bin "$codex_cargo_bin/codex-code-mode-host" --logs-client-bin "$codex_cargo_bin/logs_client"
```

Required platform resources are still built or fetched by the official package builder. No formatter, fixer, test suite, Bazel lock update, Git operation, or dependency upgrade is part of `just i`. Record its exit separately from the initial Cargo commands. A successful Cargo binary install alone does not prove a complete local CLI package or a selected source daemon.
