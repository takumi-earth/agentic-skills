# Ripwire builds, compiler selection, and installation

Read this reference only for the corresponding build or installation task. Inspect the selected checkout's current `CMakeLists.txt`, `scripts/pgobuild.sh`, or installer before relying on their behavior.

## Select the actual compiler

Inspect `CC`, `CXX`, the resolved `clang` and `clang++` executables, and `CMAKE_C_COMPILER` / `CMAKE_CXX_COMPILER` in the relevant CMake cache. Installing Homebrew LLVM or putting Clang on `PATH` does not override explicit GCC environment variables. CMake takes `CC` and `CXX` on the first configuration, then keeps the compiler paths in its cache.

Homebrew LLVM's `clang` and `clang++` are the user's selected shared defaults on this Linux setup. Use the stable formula prefix rather than a versioned `Cellar` path, and honor an explicit compiler choice for another task or host. When compiler selection is part of the authorized work, this selects the pair in the current shell:

```bash
export CC="$(brew --prefix llvm)/bin/clang"
export CXX="$(brew --prefix llvm)/bin/clang++"
```

A persistent repair belongs in the startup configuration that actually owns the assignments. On this setup, `/etc/profile.d/buildenv.sh` resolves to `~/buildenv.sh`; verify the link and current contents before editing. Session exports alone do not persist. Existing terminals and agent processes keep their inherited values, and the startup file's re-sourcing guard can prevent a simple `source` from updating them. Verify a fresh shell and give current-shell exports when needed.

For an existing CMake tree, use a fresh configuration or a separate tree when switching compilers; preserve unrelated trees and requested configuration. The current `scripts/pgobuild.sh` recreates its own trees, so a repeated GCC selection there points to incoming compiler selection rather than an old cache. Confirm that behavior in the current script before drawing the same conclusion after another pull.

Clang PGO requires a compatible `llvm-profdata` from the selected LLVM toolchain. Verify those executable paths and versions together. Inspect inherited compile and linker flags before diagnosing a subsequent configure or link failure; do not suppress diagnostics or change global flags merely to make compiler detection appear successful.

## Build the requested flavor

The repository's development tree uses no `CMAKE_BUILD_TYPE`. `Release` defines `NDEBUG`, which removes the recoverable-path traces that several gates need. Keep development and installation builds separate; use the flavor the user requested and report it accurately.

`scripts/pgobuild.sh` owns the instrumented `build_pgogen/` tree, training runs, profile merge, and optimized `build_pgo/` tree. PGO is Clang-only in this implementation. Inspect its `--cmake-extra` handling when selecting a build type; do not infer `Release` from the name of the script. Avoid reproducing only the first configure and calling the complete workflow repaired.

Do not edit source or switch branches during a build. If source changed underneath an earlier build, use the repository's clean rebuild procedure before trusting an incremental success. Validate the changed behavior through the requested workflow and the applicable repository gates; configuration success, compilation, runtime checks, and the full gate suite remain distinct evidence.

## Install without replacing canonical skills

Verify the requested new version's build before installing it, and verify the installed executable's path and `--version` afterward. Check that the installation method uses the binary and build flavor that were actually validated: the root `install.sh` currently builds a separate Release tree, so it does not install an already-built PGO binary.

The upstream installers stage vendor assets and can activate their skills automatically. For an authorized invocation of the source installer, its current no-activation path is:

```bash
RIPWIRE_NO_ACTIVATE=1 ./install.sh
```

Confirm that option in the current installer before use. Staging vendor assets does not make them canonical. Preserve harness links to the customized definitions in `~/agentic-skills`; do not run the upstream `skills/install.sh` or a generated installer recipe to replace them. Skill enhancement, new skill adoption, canonical synchronization, link changes, MCP registration, and hooks require their own requested effects and owners.

After a successfully verified installation, manually bring over skill enhancements only when the user requests that phase. Apply `$manage-ripwire-skills` in addition to `$manage-ripwire-repo` for that work, preserving customized definitions and their reviewed upstream bases.
