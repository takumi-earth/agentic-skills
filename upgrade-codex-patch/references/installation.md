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

## Preparation and the user's handoff

An upgrade-skill invocation prepares the package and stops before live replacement. Run `just i --prepare-package` with the accepted prebuilt binaries after the Cargo sequence. It assembles and validates an immutable platform package and returns `status: "prepared"` with `handoff.cwd`, `handoff.argv`, and a quoted `handoff.command`. Its `record` points to the saved preparation result under `CODEX_HOME/packages/standalone/prepared/`. It does not publish aliases, change the native daemon selection, stop processes, start services, or replace the installation receipt. Retain and publish the audited patch and guidance, then give the user that exact command. They choose when to run it; execute the handoff only on an explicit request to do so.

Directly running `just i` remains the live installation command. `--no-daemon` still publishes CLI aliases and is not a preparation substitute. Package preparation is distinct from installed or running state; do not describe it as live deployment.

On another machine, pulling `agentic-skills` obtains the installer and saved patch resources. `just i` uses the Codex source already in the selected checkout; it does not apply a patch, select an upstream tag, or upgrade dependencies. If that checkout already carries the matching release patch, use the updated installer. Otherwise complete the patch-upgrade workflow against the matching release base before running the final command.

## Installation chain

`independent installer lifetime -> selected checkouts -> native V8 setup -> official platform package build and validation -> logs_client -> compiled CLI version check -> immutable local package -> stop old runtime and helpers -> confirm process exit -> recoverable CLI aliases -> select/pin source package -> restart with saved settings -> verify executable provenance and versions -> durable receipt`.

The compiler's host triple selects the package ABI. Linux packages include the source-built `bwrap`; Windows packages include `codex-command-runner.exe` and `codex-windows-sandbox-setup.exe`. The supported builder supplies verified `rg` and the patched `zsh` where available. The installer retains `logs_client` in the package in addition to its required runtime executables.

The published package lives beneath `CODEX_HOME/packages/standalone/releases/local-<version>-<target>-<unique-id>`. Old packages remain available. Unix CLI aliases are symlinks into the complete package. Windows uses native Bun proxies so the actual Rust executable still runs inside its package and no file-symlink privilege is needed. Replaced aliases and update markers are retained as `.before-source-install-<unique-id>` backups.

A SQLite transaction serializes publication. Build or identity failures leave installed aliases untouched and clean only the installer's staging directory. An alias-publication failure restores its prior aliases. Once a package has been published, later failures retain it and report the observed installation state. The final receipt is outside the immutable package, at `CODEX_HOME/packages/standalone/source-install.json`.

By default, `just i` builds and validates the new complete package before shutting down the previous runtime. Its external process controller stops same-user Codex executables in the selected runtime's package directory, Cargo binary directory, and selected checkout's build directory, including code-mode hosts, updater/client processes, and their descendants. It excludes the independent installer's ancestry, retains captured process identities across reparenting, rechecks identities before signalling, and escalates an incomplete Unix shutdown after five seconds. It requires an empty remaining-process set before selecting or starting anything. Other users' processes and unrelated executable locations remain outside that scope; an unknown server that still owns the control endpoint remains a native lifecycle error.

Shutdown precedes alias publication: renaming a running loose binary to its backup name can change the executable path reported by the OS, and running Windows executables can obstruct replacement. Validate alias locations before shutdown, then stop the old processes while their original executable identities are available.

For an existing selection, the installer invokes `update --from-cli --yes` while the old runtime is stopped. The native command selects and pins the complete source package without launching a server in that state. It then invokes `daemon restart`, which also starts a stopped daemon while retaining saved launch settings. A fresh installation uses that same restart command's native missing-package preparation; it does not start a previous selection first. The installer does not edit native PID-registration or process-admission policy, add runtime recovery APIs, or substitute a production package.

The external selector holds Codex's existing `app-server-control/app-server-startup.lock` during package selection. Every local Unix-socket app-server takes that gate before listening, including a raw start without daemon PID registration. The selector quiesces known runtime processes while holding the gate and clears pending known starts before releasing it. This keeps a reconnecting client from reopening the endpoint during the native package copy. Unknown endpoint owners remain rejected and untouched.

Verification requires managed ownership, matching CLI/selected/running versions, a live process executing the selected daemon binary, and identical CLI, code-mode-host, and `logs_client` bytes in the source and selected packages. Any remaining Codex process in scope must execute the new source or selected package. Helpers start when the runtime needs them; the installer removes old helpers and verifies the new helper artifacts without requiring a new helper `--version` API. The receipt retains shutdown observations, startup identity, running process observations, and executable digests.

This native package selection and its restart occur when the user runs the final command, or explicitly instructs the agent to run that handoff. Preparation, skill invocation, successful validation, and publication do not grant that timing decision. Editing guidance or building a package without installation authority keeps its separate boundary.

Use `just i --no-daemon` to install the complete CLI package without starting or selecting a daemon. Use `just i --prepare-v8` to build only the V8 launcher before the upgrade's Cargo sequence.

## Execution through the daemon being replaced

The default `just i` entrypoint automatically starts an independent Python supervisor before installation. On Unix it owns a separate session; on Windows it requests a detached process outside the caller's job. Failure to establish that lifetime stops the invocation before its child installer runs. The supervisor owns the Bun installer, independent output pipes, and final result. The foreground command relays progress while attached; termination of the old Codex daemon or TUI leaves installation running.

The process controller uses Linux process metadata, macOS process enumeration and `proc_pidpath`, or Windows CIM owner information and held native process handles. Windows compares creation time at [CIM's microsecond precision](https://learn.microsoft.com/en-us/windows/win32/wmisdk/cim-datetime) when reading the native [100-nanosecond `FILETIME`](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes); it checks the executable through the held handle before termination. Keep these adapters compatible with the native host rather than assuming Linux `/proc` exists everywhere.

Each invocation reports an attempt directory under `CODEX_HOME/packages/standalone/source-install-attempts/`. It contains `invocation.json`, `stdout.log`, `stderr.log`, `supervisor.log`, and an atomically published `result.json` with native exit status and elapsed time. `--plan`, `--prepare-v8`, `--prepare-package`, and `--no-daemon` keep their direct process lifetime because they do not replace the running daemon. A failed attempt retains its logs and any already-published package; the final `source-install.json` receipt is written only after full verification.

A daemon-recovery prompt records an interruption, not command success or failure. Check whether the original installer is still running, then inspect its captured exit and `source-install.json`. A daemon running the target release can coexist with an unfinished installer and an older receipt. Continue observing a live installer; retry only when the invocation ended without completing the required installation. Correct the process lifetime before that retry, reuse the successful prebuilt binaries, and report interrupted attempts separately. Do not repeat Cargo installs or another attached `just i` merely because a tool response was lost.

## Shared features and client recovery

Package/version verification does not prove that the daemon's startup feature settings match a TUI client's requirements. Distinguish release defaults, saved daemon overrides, and the running server's feature readback. For example, upstream `0.161.0` changes the default of `api_key_model_discovery` from `false` to `true`; a daemon retaining the earlier effective value can trigger the TUI compatibility dialog without a failed package installation.

Preserve configured feature policy. Native package replacement does not itself authorize rewriting shared feature overrides to match a diagnostic. The TUI's `Restart with these settings` action applies all displayed shared values and persists them for other clients; use the user's actual selection or existing authorization for those specific changes. A screenshot is evidence, not a restart instruction. Do not generalize one host's accepted values to another.

After a restart, report the recovered turn's tool inventory separately from subsequent normal client turns. Temporary absence of `codex_tui` tools does not establish permanent removal, a dead listener, or a confirmed cause. Verify the current client handoff when needed, retaining source findings and timing inferences as separate evidence. Peer/client acceptance remains its project's own requirement; it is not an extra Cargo gate for this upgrade.

## Reuse successful upgrade builds

After both Cargo installs have succeeded, pass all three existing binaries to avoid rebuilding them:

```bash
codex_cargo_bin="${CARGO_HOME:-$HOME/.cargo}/bin"
just i --prepare-package --entrypoint-bin "$codex_cargo_bin/codex" --code-mode-host-bin "$codex_cargo_bin/codex-code-mode-host" --logs-client-bin "$codex_cargo_bin/logs_client"
```

Required platform resources are still built or fetched by the official package builder. No formatter, fixer, test suite, Bazel lock update, Git operation, or dependency upgrade is part of `just i`. Record its exit separately from the initial Cargo commands. A successful Cargo binary install alone does not prove a complete local CLI package or a selected source daemon.

When a Linux `bwrap` has already been built for the selected package, pass `--bwrap-bin <executable>` as well. The official builder still validates the complete package. Reuse only binaries with established provenance for the accepted source; do not reuse a rejected implementation's binaries merely because their version strings match.

## Installer repair acceptance

Keep installation orchestration in this package. Before expanding the carried Codex patch, trace whether its existing native commands already meet the requirement when called in the correct order and from an independent process. A managed-start shortcut, a changed admission rule, or a helper API added solely for installer assertions creates avoidable fork maintenance.

Run the existing Bun installer tests and `python3 upgrade-codex-patch/scripts/test_source_install.py` from the canonical skills repository when changing these scripts. The latter exercises independent outcome capture, launching-session exit, scoped native process shutdown, unrelated-process preservation, and reparented identity. These are installer tests, separate from the Codex repository's prohibited test commands.

For real workflow evidence, run `test_install_runtime.py` with complete accepted old and new packages and the actual selected checkout. It invokes the imported `just i` recipe against isolated runtime and Cargo homes. Require an older registered runtime and an older runtime with missing PID registration, each with an active old code-mode host, to be stopped and replaced without a manual kill or `/daemon`. Include a fresh-home case that preserves saved feature settings and a foreign endpoint owner that remains alive and rejected. Record process exits, selected/live executable provenance, helper artifacts, command exit, and durable outcome. Code must target macOS, Linux, and Windows; native macOS/Windows verification may be performed in the user's sessions on those hosts.
