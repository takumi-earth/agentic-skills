# Typed consumer compatibility and lifecycle

Use this reference after selecting the producer contract in `typed-goal-artifact-contract.md`. Completing this specification does not select a producer for deployment, change goal state, or install a hook.

## Absence and compatibility

| Input situation | Consumer behavior |
| --- | --- |
| Valid metadata from the explicitly selected producer, bound to the current goal | Resolve the producer-selected file under its declared locator contract. |
| Version 1 selection is `none` | Report no selected file; do not parse prose or select a historical/output record. |
| Version 1 selection is `unavailable` | Report unavailable association; preserve its reason. |
| Metadata omitted by a declared legacy producer | Permit the existing legacy resolver only when the caller explicitly selected the legacy compatibility policy and the current objective/task supplies an attributable exact designation. |
| Required version 1 field missing, present `null`, invalid record, unsupported version/kind, conflicting producers, or stale binding | Report the specific failure; never silently downgrade to objective-prose inference. |
| Current user independently designates an exact path | The caller may choose the existing explicit-path operation under that current authority. This is a separate input mode, not an inferred fallback from bad typed data. |

A legacy compatibility policy is an explicit deployment/task choice, not a Boolean read from untrusted metadata. Its resolver uses the declared environment/root and exact-selection boundaries. A path mentioned in history or an assistant-authored label cannot supply the missing user designation. Normalized display text never changes which filesystem object was selected.

New metadata fields can break strict old decoders even when `ThreadGoal` itself is unchanged. A selected adapter must validate its producer profile and preserve unknown/unsupported information as a failure or an explicitly inert record. Do not silently strip fields and write the stripped result back to durable state. No consumer upgrade here authorizes registering a new producer, rewriting stored goals, or enabling a legacy fallback.

## Lifetimes stay distinct

| Event | Durable profile | Response-only profile |
| --- | --- | --- |
| Status-only change, including completion | Preserve the stored association and objective revision. Recheck only the applicable current filesystem facts. | Use metadata supplied for that exact invocation. Status alone supplies no designation. |
| Objective edit with the same goal ID | Require the new objective revision/hash and explicitly rebound selection; earlier metadata is stale. | Compare the returned snapshot and current authority; a prior response is not a replacement input. |
| Replacement goal | Require the new goal identity; never reuse the previous goal's selection merely because paths/text match. | Old response metadata remains historical, even if its timestamp is recent. |
| Resume without an earlier response | Read the authoritative stored association; do not scan the transcript to reconstruct it. | Association is unavailable unless a new invocation receives attributable input. Do not invent durable caching. |
| Fork | Consume only the association explicitly rebound by the authorized fork contract to the child goal/thread. | Parent response metadata does not authenticate a child invocation. |
| Cross-machine or custom-runtime move | Resolve only through the trusted current storage/namespace mapping. Preserve an unresolved reference when no mapping exists. | Apply the same locator boundary to the current event; copied home-relative strings are not local authority. |
| Deleted or unavailable file | Preserve the user selection and report availability failure. | Preserve the observation and report availability failure. |

Neither profile changes protected user decisions, authorizes file restoration, or marks a goal complete. Replay handling follows the existing authorized workflow; no new persisted receipt or audit ledger is required by this consumer.

## Attributed source and evaluation boundary

At `~/rust-forks/codex-orig` revision `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`, complete reads of `codex-rs/state/src/model/thread_goal.rs`, `codex-rs/state/src/runtime/goals.rs`, `codex-rs/ext/goal/src/tool.rs`, and `codex-rs/hooks/src/events/post_tool_use.rs` established the relevant state, response, and pass-through seams. The current response projection drops internal goal identity and carries no typed artifact association. A future selected producer must supply the identity fields this consumer requires. The corrected producer references give the concrete integration maps; this consumer must not manufacture their missing output.

Evaluate zero/one/multiple records; selected plus historical/output roles; duplicate IDs/locators; unknown tags and versions; present-null versus legacy absence; exact external and relative paths; missing current authority; stale/replayed/mismatched responses; both producer fields; resume without old metadata; fork rebinding; and deleted/unmapped files. These are specification cases evaluated locally, not an independent evaluator, Codex build, live hook event, or migration test. Structural package validation establishes package form only. Keep diagnostics in the existing response or authorized record and preserve the hook's channel/silence contract.
