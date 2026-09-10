# Runtime-context producer and consumer map

The following source files were read completely at `~/rust-forks/codex-orig`, revision `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`, with no working-tree differences in the inspected files. This attributes source observations only; it does not establish which binary is running. Earlier `codex-source-findings.json` and running-binary statements in candidate provenance remain historical evidence.

| Source and symbol | Observed responsibility | Proposed version 1 integration |
| --- | --- | --- |
| `codex-rs/hooks/src/events/post_tool_use.rs`: `PostToolUseRequest`, `command_input_json`, `run` | Carries event identity, working directory, tool input and response; serializes one input before executing matched handlers. There is no typed runtime root. | Accept a trusted runtime context separately from tool payloads and serialize it only for the selected input profile. Preserve session, turn, and tool-call binding. |
| `codex-rs/hooks/src/schema.rs`: `PostToolUseCommandInput`, `write_schema_fixtures` | Declares the strict input schema and generates its fixtures. | Add the selected profile's typed field and generated schema together. Preserve the legacy profile for strict old consumers. |
| `codex-rs/hooks/src/engine/command_runner.rs`: `CommandHookRuntime::new`, `build_command` | Replays a supplied session environment snapshot, then applies handler environment overrides. It is not a typed root producer. | The runtime constructing the request must supply the resolved root and trusted namespace/home binding. Do not mistake an overridden child environment for that authority. |

The specification introduces a required trusted launcher binding; the inspected code does not currently provide it. This map identifies integration seams, not an implementation-ready claim that every upstream configuration handoff has already been traced. A future authorized implementation must connect the session's actual resolved configuration to those seams and test the selected supported launch contexts.

The existing downstream owner was read completely at `~/agentic-skills`, revision `c761c38`:

| Source and symbol | Current responsibility |
| --- | --- |
| `maintain-living-goal/scripts/goal_artifact_resolution.py`: `resolve_runtime_root`, `resolve_artifact`, `resolve_designated_artifact` | Shared pure resolution, environment fallback, managed containment, and exact caller-designated path validation. A future event-root adapter belongs here. |
| `maintain-living-goal/scripts/goal_completion_handoff_hook.py`: `build_output` | Consumes resolution for the completion handoff and presents the selected hook envelope. |
| `auto-skill-enhancer/scripts/post_goal_review_hook.py`: `load_shared_resolver`, `resolve_goal` | Loads the shared resolver as a consumer; package lookup selects code resources, not runtime state. |

This package contains an inert specification. No producer, consumer, hook registration, configuration, or installed runtime was changed by completing it. Future validation must separately establish schema serialization, profile compatibility, trusted root provenance, and supported resume/fork behavior; structural package validation establishes none of those runtime effects.
