# Response producer and consumer map

The following files were read through EOF without working-tree differences at `~/rust-forks/codex-orig`, revision `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`. This identifies source seams; it does not verify the running binary. Historical checkout and diagnostic claims remain provenance, not proof of a current deployment.

| Source and symbol | Observed behavior | Proposed integration |
| --- | --- | --- |
| `codex-rs/ext/goal/src/tool.rs`: `GoalToolResponse`, `goal_response`, `GoalToolResponse::new` | Emits the goal and budget fields; no artifact sidecar exists. | Construct the versioned response extension from the operation's committed snapshot and trusted invocation artifact input. |
| Same file: `handle_get`, `handle_create`, `handle_update`, `protocol_goal_from_state` | Reads or mutates state, then converts the result. The conversion drops the internal goal ID. Update arguments contain status only. | Preserve the internal ID for response binding before projection; do not infer an artifact designation from a status argument or refetch a different snapshot for metadata. |
| `codex-rs/state/src/model/thread_goal.rs`: `ThreadGoal` | Holds the internal goal ID and objective with no artifact field. | Read the returned snapshot's identity; leave durable artifact state unchanged in this alternative. |
| `codex-rs/hooks/src/events/post_tool_use.rs`: `PostToolUseRequest`, `command_input_json` | Copies `tool_response` as a JSON value and carries session, turn, and tool-call IDs. | Preserve the selected response profile and independently check its binding. Do not manufacture missing metadata in the hook. |
| `codex-rs/hooks/src/schema.rs`: `PostToolUseCommandInput` | Accepts a structured response value within a strict event input shape. | Preserve the surrounding event contract; test the nested response profile as well as the event schema. |

The proposed `GoalArtifactInput` is a required future producer input, not a capability found in those files. Its implementation must connect an actual user-input/attachment selector to the invocation. If that path cannot supply attributable data, the defined result is `unavailable`; moving a prose parser upstream does not satisfy that input contract.

The current Python consumer files were also read completely at `~/agentic-skills`, revision `c761c38`: `maintain-living-goal/scripts/goal_artifact_resolution.py` owns pure selection and filesystem validation, `maintain-living-goal/scripts/goal_completion_handoff_hook.py` owns handoff presentation, and `auto-skill-enhancer/scripts/post_goal_review_hook.py` consumes the shared resolver. A selected future typed adapter belongs with that resolver; the enhancer must not become a competing selection owner.

Before an authorized implementation is enabled, its own command matrix must establish response serialization, invocation/snapshot binding, missing-input behavior, strict-client compatibility, pass-through, and resume limitations. This correction completed an inert specification only. No Codex source, goal state, hook registration, or runtime configuration was changed, and no Codex build or live hook event was run.
