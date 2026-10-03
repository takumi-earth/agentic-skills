---
name: locate-strict-repos
description: "Locate and verify strict ecosystem repository checkouts on macOS, Linux, Windows, and WSL. Use when a needed owner's local path is unknown, missing, or stale. Reuse verified locations; do not run discovery for an already located owner or turn it into ecosystem adoption."
---

# Locate Strict Repos

Resolve the local checkout of the owner needed for the current task. This skill owns repository discovery for the strict ecosystem; callers use its result rather than maintaining their own expected-path rules.

## Start with local evidence

- Identify the needed repository or crate from the current task, owning manifests, dependency source declarations, or repository guidance. Include template, fragment, and maintained fork owners when relevant; a directory named `strict-*` is not the only possible owner.
- Reuse a user-supplied or previously verified location on the same host. Recheck existence and identity when it may be stale; do not rediscover unchanged locations on every phase.
- Determine the execution host and filesystem. An agent running on Linux through a macOS client uses Linux paths. Treat WSL and native Windows as distinct environments.
- Inspect the active checkout, its workspace/path dependencies and local Git worktree metadata, and repository roots already evidenced in the session or local project configuration. Resolve symlinks before interpreting package-relative paths.

A suggested path is a candidate, not an established location. `~/strict-rs` is a convention to check when relevant; its absence does not establish that the repositories are missing.

## Search on the current platform

Prefer evidenced roots over the candidates below. Check candidate roots for existence before searching them, and expand home variables on the execution host rather than substituting a remembered username.

- **macOS:** Check evidenced repository roots on mounted volumes as well as home directories. On this user's setup, `/Volumes/ExternalData/Library/Git` is an observed root; verify the volume is available. Other candidates are `~/strict-rs`, `~/git`, and `~/src`. Use `rg --files` within selected roots to locate manifests and repository guidance.
- **Linux:** Check declared workspace roots and any explicitly configured data-volume paths, then existing candidates such as `~/strict-rs`, `~/git`, and `~/src`. Use `rg --files` within those roots. Do not infer `/Volumes/...` paths from a macOS session or probe another host merely because it has a similar project.
- **Windows:** Use the current host's `$HOME` or `$env:USERPROFILE`, declared workspace roots, and evidenced repository drives. Candidates include `strict-rs`, `git`, and `source\repos` beneath that home. Use `rg --files` when available, or `Get-ChildItem` with an explicit root and depth bound; do not recursively scan every drive or network share.
- **WSL:** Search Linux workspace roots first. Inspect a Windows checkout through `/mnt/<drive>/...` only when its actual Windows location is supplied or evidenced. A native Windows path and a WSL path are not interchangeable, and neither proves the other checkout exists.

Search each selected root once for the needed owner. Keep traversal within those repository roots, omit build output and dependency trees, and inspect manifest identities rather than relying only on folder names. Do not expand into the entire home directory, filesystem, all mounted volumes, or other machines to avoid requesting a missing location.

## Verify a candidate

- Resolve its real path and Git root using local metadata, such as `git -C <candidate> rev-parse --show-toplevel`; account for linked worktrees and nested workspaces.
- Check the relevant workspace/member manifests and repository guidance against the required owner. If source identity matters, compare local Git remote metadata with the already evidenced dependency source without contacting the remote or printing embedded credentials.
- When multiple checkouts match, use the one selected by the user or active workspace. If they differ materially and neither is selected, report the candidates and ask which to use rather than choosing the newest-looking directory.
- Retain the verified owner-to-path association in current task context. Read that owner's applicable `AGENTS.md` before dependent implementation. Locating it does not grant write, verification, dependency, or Git authority there.

## When the owner cannot be located

Distinguish an absent candidate path, an unavailable mount, denied access, ambiguous checkouts, and an owner not found within the searched roots. Report the relevant roots and unresolved owner; do not make a machine-wide absence claim from a bounded search.

Request the local checkout path or missing mount/access information when it blocks the task. Continue independent authorized work. Do not substitute an old consumer/template checkout as the current owner; label any usable cached or secondary source by its actual provenance and limits.

Remote source access is a separate fallback. It can proceed under existing user authorization covering the repository, destination, purpose, and disclosure involved; do not ask again when that authority is already established. If it is absent or unclear, request the local path or approval for a specific remote fallback before sending private identifiers.

Read-only network requests disclose their destinations and request contents. A missing local path does not authorize `gh`, Git network commands, web search, cloning, or installation. Keep private owner discovery local unless the user authorizes that disclosure to the external service involved.

For an authorized remote fallback, use the exact source identity already established from the user or local metadata. Inspect the repository layout before requesting files, use the actual response format, and stop on an unresolved identity instead of guessing names and paths. Keep the lookup limited to the current need; it does not authorize adopting ecosystem tooling or changing dependencies.

Return the located path and identity, or the scoped unresolved condition and next required input. Do not create a persistent locator report or configuration unless the task requests one.
