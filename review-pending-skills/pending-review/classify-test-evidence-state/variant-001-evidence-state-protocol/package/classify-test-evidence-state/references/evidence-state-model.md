# Test evidence-state model

Evidence observations are monotonic but non-substitutable.

| State | Minimum evidence | Does not prove |
| --- | --- | --- |
| `declared` | Planned test or gate is named | Source exists |
| `written` | Current test source exists | Compilation or execution |
| `compiled` | Named build/configuration accepted it | Test body ran |
| `executed` | Named command reached the test | Assertions passed |
| `assertions-passed` | Assertions in the named scope passed | Process exit `0` |
| `process-passed` | Command exited `0` | Canonical scope or adequacy |
| `focused-gate-passed` | Named focused gate exited `0` | Broader canonical gate |
| `canonical-gate-passed` | Repository-declared canonical command exited `0` | Unrelated product behavior |

## Transition rules

- Record command identity, scope, configuration, timestamp, process exit, and evidence locator for every executed state.
- Preserve `assertions-passed` plus `process-failed` when inner checks succeed but the final process exits nonzero.
- Preserve `written-unexecuted` when verification is forbidden or unavailable; do not call it failure or coverage.
- Do not infer canonical acceptance from a focused gate, static scan, worker verdict, or test source.
- Close a behavioral claim only when executed evidence observes its named semantic or product owner.

## Precise language

Prefer `test written; execution not authorized`, `focused process passed; canonical gate unrun`, or `assertions passed; process exited 1` over `covered`, `verified`, or `tests pass`.
