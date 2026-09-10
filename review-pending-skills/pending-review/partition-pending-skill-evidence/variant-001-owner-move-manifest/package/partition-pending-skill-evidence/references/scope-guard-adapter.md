# Scope Guard Adapter

Use `scripts/run_home_normalized_skill_guard.py` as an adapter around the canonical `skill_change_guard.py` when an authorized snapshot requires exclusive publication. The canonical guard already normalizes paths; the distinct adapter behavior is conflict protection.

## Contract

- Invoke the environment-selected `python3`; do not hard-code an interpreter path.
- Pass the canonical scope guard through `--guard` and its unchanged arguments after `--`.
- For `snapshot`, accept `--output PATH` and `--output=PATH` with the canonical last-value rule. Enforce the selected skills-root scratchpad boundary before creating the intermediate manifest, then publish the requested final snapshot without replacement. Normalize adapter diagnostics without changing native guard outcomes.
- For `unchanged` and `verify`, pass the home-normalized snapshot to the canonical guard and normalize emitted paths without changing its exit status.
- Do not redirect caches, temporary directories, or command behavior to work around sandbox or permission failures.

## Evidence boundary

The snapshot and command report are run-specific evidence instances and remain in `.scratchpad/`. This adapter is a reusable product script and therefore belongs to the pending package.

## Validation

- Run a successful snapshot and confirm the persisted manifest contains `~/...` rather than an expanded user-home prefix.
- Run `unchanged` against that manifest and require exit code `0` when no targeted package changed.
- Run `verify` with exact allowlisted changes and require unexpected paths to be empty.
- Run a failing verification fixture and preserve its nonzero exit as a diagnostic result.

Adapter input, conflict, and operational failures emit one structured `adapter-failure` result and exit `2`. Native guard success and failure retain their original stdout, stderr, and exit status after path presentation. The adapter cleans up its own intermediate file, including on child failure; it does not change the canonical guard's implementation or create recording authority.
