# Runtime context contract, version 1

This is a proposed input extension for `PostToolUse`, not a description of an installed Codex protocol. It supplies runtime location only. It does not identify a goal artifact, verify a user designation, or remove the need for a separate artifact-selection contract.

## Wire fields and producer

A handler using the proposed `codex-runtime-context/v1` input profile receives the existing event plus one required `runtime_context` object. Legacy profiles omit that property entirely. The object has exactly these fields; duplicate JSON keys, unknown fields, and `null` values are invalid in version 1.

```typescript
type RuntimeContextV1 = {
  schema_version: 1;
  namespace_id: string;
  home_id: string;
  path_style: "posix" | "windows";
  codex_home: string;
};
```

- `schema_version` is the JSON integer `1`, never a Boolean or a numeric string.
- `namespace_id` identifies the filesystem namespace in which this Codex runtime resolves paths. `home_id` identifies the runtime user's home within that namespace. Both are nonempty opaque identifiers supplied by the trusted launcher, not by a model tool argument, objective text, or a hook's environment override. They are context bindings, not authentication credentials or portable artifact identities.
- `path_style` defines the pathname grammar. `codex_home` is one nonempty, NUL-free, absolute runtime pathname after expansion. Serialize a path beneath the producer's user home as `~/...` (or `~` for that home itself); otherwise use an absolute path in the declared grammar. A similarly prefixed sibling directory is not beneath that home.
- The producer obtains the root from the running session's resolved configuration. It does not derive it from the executable, skill checkout, installed package, transcript filename, or process working directory. A custom configured root is valid.
- There is one root authority. Version 1 derives the managed attachment directory as `codex_home / "attachments"`; it does not accept a second independently supplied `attachments_root`. A future independently configurable attachment root requires a new contract version.

Example of the extension object, without the surrounding existing event fields:

```json
{
  "runtime_context": {
    "schema_version": 1,
    "namespace_id": "local-runtime-filesystem",
    "home_id": "runtime-user-home",
    "path_style": "posix",
    "codex_home": "~/codex-custom"
  }
}
```

## Trust, home expansion, and precedence

The dispatch channel must independently bind the event to its runtime namespace and home. Matching self-declared identifier strings is insufficient. The version 1 local-launch profile is supported only when the launcher establishes that producer and handler share the same filesystem, path grammar, and user-home mapping. Preserve that mapping even if a handler overrides `HOME` or `CODEX_HOME`. If the launcher cannot establish it, do not deliver this profile as a usable authority source.

`~` means the producer's home under that binding, not whichever home the consumer happens to use. A copied event, another machine, a remote execution namespace, or an unbound launcher yields `unbound-runtime-context`; never expand its `~` against the reader's home. An explicitly supplied trusted namespace mapping would be a separately selected transport profile, not an inferred version 1 capability.

| Input observation | Consumer result |
| --- | --- |
| Supported, bound event context and absent or equal `CODEX_HOME` | Select the event root; report `event-runtime-context` as its source. |
| Supported, bound event context and different inherited `CODEX_HOME` | Select the event root and disclose the environment conflict. An environment override cannot replace runtime configuration. |
| Context omitted by an explicitly supported legacy event profile | Apply only that consumer's declared environment fallback. |
| Context omitted under the negotiated version 1 profile | `missing-runtime-context`; no fallback. |
| Present `null`, wrong type, empty root, relative root, duplicate key, or conflicting/unknown field | `invalid-runtime-context`; no fallback. |
| Unrecognized version or pathname grammar | `unsupported-runtime-context`; no fallback. |
| Correctly shaped root that is missing, not a directory, or unusable for managed attachments | Preserve `invalid-runtime-root` from the filesystem resolver; do not search another root. |

Presentation normalization changes path spelling at actual component boundaries only. Preserve unrelated text and source bytes. Root metadata says where to look; filesystem inspection still owns existence and containment observations.

## Compatibility and lifetime

Input-profile selection is an explicit producer/consumer deployment choice. A producer must not send the new property to an old handler merely because some JSON parsers ignore unknown fields. Strict legacy consumers continue receiving the old input shape; a version 1 consumer requires the new shape. Unknown-field behavior is specified separately for each profile. Do not silently downgrade a selected version 1 event when its context is invalid.

At the inspected source revision, the hook dispatcher constructs one input JSON string before executing matched handlers. Supporting mixed legacy and version 1 handlers therefore requires profile-aware serialization or a uniformly negotiated handler set. Merely adding a field to the Rust struct does not establish compatibility.

Recompute context from the runtime executing a resumed session or a supported fork. Never replay a prior machine's root as current configuration. This extension does not persist an artifact association through resume or transfer a parent's task authority to a child.

## Contract examples to evaluate before implementation

Evaluate default and custom roots; equal and conflicting environment values; absent legacy versus missing negotiated fields; present `null`; relative and sibling-prefixed paths; strict legacy handlers; mixed handler profiles; resumed execution under a different root; and an event copied to another home or filesystem. These are specification cases, not claims that Codex serialization or live hooks have been executed.
