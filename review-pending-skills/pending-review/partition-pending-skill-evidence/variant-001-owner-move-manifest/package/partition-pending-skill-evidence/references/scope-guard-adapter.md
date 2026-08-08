# Scope Guard Adapter

Use `scripts/run_home_normalized_skill_guard.py` only as an adapter around the canonical `skill_change_guard.py` command when its snapshot must remain portable beneath the user home.

## Contract

- Invoke the environment-selected `python3`; do not hard-code an interpreter path.
- Pass the canonical scope guard through `--guard` and its unchanged arguments after `--`.
- For `snapshot`, intercept the temporary raw manifest, normalize the user-home prefix to `~`, and create the requested final manifest without overwriting an existing artifact.
- For `unchanged` and `verify`, pass the home-normalized snapshot to the canonical guard and normalize emitted paths without changing its exit status.
- Do not redirect caches, temporary directories, or command behavior to work around sandbox or permission failures.

## Evidence boundary

The snapshot and command report are run-specific evidence instances and remain in `.scratchpad/`. This adapter is a reusable product script and therefore belongs to the pending package.

## Validation

- Run a successful snapshot and confirm the persisted manifest contains `~/...` rather than an expanded user-home prefix.
- Run `unchanged` against that manifest and require exit code `0` when no targeted package changed.
- Run `verify` with exact allowlisted changes and require unexpected paths to be empty.
- Run a failing verification fixture and preserve its nonzero exit as a diagnostic result.
