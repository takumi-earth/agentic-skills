# Event-root consumer contract

This is an inert consumer specification for the proposed `codex-runtime-context/v1` profile. Its paired producer is `define-codex-goal-artifacts/variant-001-post-tool-use-codex-home`, corrected in `516fe93`. Pairing the specifications does not select or install that Codex protocol.

Read the [version 1 producer contract](../../../../../define-codex-goal-artifacts/variant-001-post-tool-use-codex-home/package/define-codex-goal-artifacts/references/post-tool-use-schema.md) when integrating this profile. The required extension is exactly:

```typescript
type RuntimeContextV1 = {
  schema_version: 1;
  namespace_id: string;
  home_id: string;
  path_style: "posix" | "windows";
  codex_home: string;
};
```

`schema_version` is integer `1`, never Boolean; identifiers and paths are nonempty strings. No unknown fields, duplicate keys, or `null` values are valid. `codex_home` is absolute after expansion in the declared grammar. `attachments` is derived from that root; `attachments_root` is not an independently accepted field. The trusted launch channel binds namespace and home; matching JSON labels alone does not authenticate them. `~/...` refers to the producer's bound home and is never expanded using an unrelated consumer home.

## Select the request mode before resolution

The caller supplies an established current goal designation and chooses one of these independent modes. A failed managed lookup never changes modes implicitly.

| Mode | Selected input and checks |
| --- | --- |
| Exact user path | A current explicit user designation supplies one path and, if relative, an established absolute base directory. Call the shared `resolve_designated_artifact` path boundary. Any filename or extension and paths outside attachments are valid. Runtime-root metadata is not needed for this independent input. |
| Managed objective reference | Use the exact current managed reference selected by the goal's task contract, together with the chosen event/legacy runtime authority. Require canonical containment and the existing `<uuid>/<filename>` managed shape. Root metadata alone never selects the artifact. |

Do not infer a designation from arbitrary historical paths, recursively searched JSON fields, or an assistant-authored role label. A bare filename such as `goal` is valid when explicitly supplied as the selected path; prose extraction need not recognize every filename to support this mode. Capture the base when the user designates a relative path. Do not use a resumed process's working directory or package directory as a replacement base.

## Resolve managed authority

1. Identify the input profile from the trusted dispatch/consumer contract, not from payload text claiming to be versioned.
2. For version 1, require a valid bound `runtime_context`. Prefer its root over inherited `CODEX_HOME`; disclose a conflict without switching authorities. Invalid, unsupported, missing negotiated, or unbound context is a typed failure, never an environment fallback.
3. Only for a declared legacy profile with no context field, use the fallback rules in `compatibility-fallback.md`. A present invalid context is not legacy absence.
4. Expand the selected root in its trusted home/namespace and apply the shared resolver's existing directory and attachment-root checks. A custom root is valid. Missing directories, an attachment-root symlink, or unusable authority fails without searching another root.
5. Resolve the selected managed reference. Require canonical containment beneath the chosen attachment root, exactly `<uuid>/<filename>`, no traversal, and a regular non-symlink final file. Do not require `pasted-text-1.txt`, a particular extension, or a directory scan. Retain the actual selected object through normalization.
6. Return the existing `GoalArtifactResolution` shape. Use `approach: "event-root"` for this proposed path, preserve stage/code/condition/expected/received facts, and include root-source/conflict observations in the existing diagnostic values. Do not pretend event authority came from an environment variable or mutate `os.environ` to simulate it.

A valid root and valid reference do not prove the current task authorized reading, writing, restoring, or completing anything. The resolver reports selection and filesystem observations; the caller preserves authority and the hook's output/silence contract.

## Current source ownership

At `~/agentic-skills` revision `c761c38`, these files were read completely: `maintain-living-goal/scripts/goal_artifact_resolution.py`, `maintain-living-goal/scripts/goal_completion_handoff_hook.py`, and `auto-skill-enhancer/scripts/post_goal_review_hook.py`. The first owns pure resolution; the other two are presentation/workflow consumers. Extend the shared owner if this alternative is later implemented. The enhancer's sibling-package lookup finds code resources only and must not become another runtime-root resolver.

The producer seams were read at `~/rust-forks/codex-orig` revision `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`: `codex-rs/hooks/src/events/post_tool_use.rs` (`PostToolUseRequest`, `command_input_json`), `codex-rs/hooks/src/schema.rs` (`PostToolUseCommandInput`), and `codex-rs/hooks/src/engine/command_runner.rs` (`CommandHookRuntime`, `build_command`). These files do not implement the proposed typed root or trusted profile binding. The source observation does not establish a running binary or cross-platform execution.
