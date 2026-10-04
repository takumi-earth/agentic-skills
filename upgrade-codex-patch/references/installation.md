# Complete source-package installation

The package's `justfile` owns `just i`. Import it from the Codex checkout with:

```just
import? x'${AGENTIC_SKILLS_REPO:-~/agentic-skills}/upgrade-codex-patch/justfile'
```

Use Just `1.32` or newer and Bun `1.4.1` or newer. The recipe uses a Bun script
interpreter rather than the Codex checkout's Python shell adapter. The actual
package build still uses Codex's supported Python `3.11+` package builder.

The installer probes that interpreter's native certificate paths. When its
default CA bundle is missing, no `SSL_CERT_FILE` or `SSL_CERT_DIR` override is
supplied, and the host is Unix, it selects an existing system CA bundle for its
child processes. Certificate verification remains enabled. Existing Python
defaults and explicit certificate overrides are preserved; Windows retains
Python's native certificate-store behavior. The selected fallback is reported
before package assembly and does not change global shell or interpreter settings.

## Location authority

| Location | Selection |
| --- | --- |
| Skill resources | The imported justfile's `source_directory()`; `AGENTIC_SKILLS_REPO` selects the import, with `~/agentic-skills` as its default |
| Codex checkout | `CODEX_REPO_ROOT`, already exported by the checkout's root justfile; required for direct skill invocation |
| V8 checkout | `CODEX_V8_REPO` when set; otherwise the checkout's configured Cargo wrapper path, then a sibling `codex-v8` |
| Runtime state | `CODEX_HOME`, with the CLI's usual `~/.codex` default |
| Installed CLI aliases | `CARGO_HOME/bin`, with `~/.cargo/bin` as the Cargo default |
| Python interpreter | `CODEX_INSTALL_PYTHON`, defaulting to `python3` on Unix and `python` on Windows |

Use absolute paths or `~/...` for explicitly supplied repository locations.
An explicit invalid V8 location fails; it does not silently select another checkout.
The installer passes the resolved native wrapper through `RUSTC_WRAPPER` to child
builds without rewriting the checked-in Cargo configuration. It selects the Bun
running the installer for helper processes, including when `CODEX_V8_BUN` chooses
a different compatible executable.

```bash
export AGENTIC_SKILLS_REPO=~/work/agentic-skills
export CODEX_V8_REPO=~/work/codex-v8
just i --plan
just i
```

`--plan` reads the selected inputs and compiler host and prints their normalized
JSON without installing, building the launcher, or starting services.

## Installation chain

`selected checkouts -> native V8 setup -> official platform package build and
validation -> logs_client -> compiled CLI version check -> immutable local
package -> recoverable CLI aliases -> native daemon selection/pinning -> version
verification`.

The compiler's host triple selects the package ABI. Linux packages include the
source-built `bwrap`; Windows packages include `codex-command-runner.exe` and
`codex-windows-sandbox-setup.exe`. The supported builder supplies verified `rg`
and the patched `zsh` where available. The installer retains `logs_client` in the
package in addition to its required runtime executables.

The published package lives beneath
`CODEX_HOME/packages/standalone/releases/local-<version>-<target>-<unique-id>`.
Old packages remain available. Unix CLI aliases are symlinks into the complete
package. Windows uses native Bun proxies so the actual Rust executable still
runs inside its package and no file-symlink privilege is needed. Replaced aliases
and update markers are retained as `.before-source-install-<unique-id>` backups.

A SQLite transaction serializes publication. Build or identity failures leave
installed aliases untouched and clean only the installer's staging directory.
An alias-publication failure restores its prior aliases. Once a package has been
published, later failures retain it and report the observed installation state.
The final receipt is outside the immutable package, at
`CODEX_HOME/packages/standalone/source-install.json`.

By default, `just i` starts the managed app-server when necessary, then invokes
`update --from-cli --yes` and verifies the CLI, selected daemon and running daemon
versions. This can restart a managed daemon. The native daemon owner decides
whether the existing server is managed; the installer never kills an unmanaged
server or substitutes a production release for the source build.

Use `just i --no-daemon` to install the complete CLI package without starting or
selecting a daemon. Use `just i --prepare-v8` to build only the V8 launcher before
the upgrade's Cargo sequence.

## Reuse successful upgrade builds

After both Cargo installs have succeeded, pass all three existing binaries to
avoid rebuilding them:

```bash
codex_cargo_bin="${CARGO_HOME:-$HOME/.cargo}/bin"
just i \
  --entrypoint-bin "$codex_cargo_bin/codex" \
  --code-mode-host-bin "$codex_cargo_bin/codex-code-mode-host" \
  --logs-client-bin "$codex_cargo_bin/logs_client"
```

Required platform resources are still built or fetched by the official package
builder. No formatter, fixer, test suite, Bazel lock update, Git operation, or
dependency upgrade is part of `just i`. Record its exit separately from the
initial Cargo commands. A successful Cargo binary install alone does not prove
a complete local CLI package or a selected source daemon.
