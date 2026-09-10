# Durable goal artifact contract, version 1

This specification proposes optional `ThreadGoal.managedObjectiveArtifacts` metadata. The historical field name does not restrict a user-designated goal file to the managed attachment directory. Human `objective` text remains unchanged. The package does not implement a Codex protocol.

## Exact native wire shape

A present field contains the following object. Every property shown without `?` is required; `null`, unknown fields, duplicate JSON keys, unknown tags, and Boolean values in integer fields are invalid. TypeScript notation describes the proposed wire contract; it is not an executable validator.

```typescript
type GoalArtifactSetV1 = {
  schemaVersion: 1;
  threadId: string;
  goalId: string;
  objectiveRevision: number;
  objectiveSha256: string;
  selection: Selection;
  artifacts: Artifact[];
};
type Selection =
  | { state: "selected"; artifactId: string; designation: Designation }
  | { state: "none" }
  | { state: "unavailable"; reason: "legacy" | "no-authoritative-input" };
type Designation = {
  source: "user-path" | "managed-objective-input";
  inputId: string;
};
type Artifact = {
  artifactId: string;
  role: "current-objective" | "historical-input" | "output";
  locator: Locator;
};
type Locator =
  | { kind: "managed-file"; storageId: string; relativePath: string }
  | {
      kind: "designated-file";
      namespaceId: string;
      homeId: string;
      pathStyle: "posix" | "windows";
      path: string;
      baseDir?: string;
    };
```

All identifiers are nonempty opaque strings. `objectiveRevision` is an integer in `1..=2^63-1`, not a Boolean; it changes when the stored objective changes, including an edit that later restores earlier text. `objectiveSha256` is 64 lowercase hexadecimal characters hashing the exact stored objective's UTF-8 bytes, after any existing input normalization. It binds metadata to objective text, not to mutable goal-file contents. Status, accounting, and updated timestamps do not define artifact identity.

The state producer takes `threadId` and the existing internal `goalId` from the committed goal snapshot. It obtains `Designation` from the trusted user-input/attachment-selection path for that operation. `inputId` must resolve to that actual designation in the producer's input context. A model-authored objective, role label, or provenance string is not that input. If no attributable designation is available, emit `unavailable`, not a guessed selection.

## Selection and file identity

- `selected` names exactly one record with role `current-objective`. That is the only `current-objective` record. Its verified designation must select that exact locator for this goal and objective revision. It remains the goal's objective artifact even when the goal is paused or complete.
- `none` means the producer knows this objective deliberately has no selected file. `unavailable` means the producer lacks authoritative selection information. Both allow historical/output records but prohibit a `current-objective` record.
- Artifact IDs are unique within the set. Repeating an ID, even with identical bytes, is invalid. Duplicate normalized locators are invalid producer output; do not invent a priority by array order. Distinct files with equal contents may represent distinct scenario roles.
- A historical input or output never becomes current merely because it is the only existing file. Unknown roles or locator kinds make version 1 unsupported/invalid; never discard them to manufacture a single candidate.
- `managed-file.relativePath` is exactly `<uuid>/<filename>` beneath the attachment store identified by `storageId`. Use two nonempty slash-delimited components, a UUID first component, and no traversal, NUL, backslash, or absolute prefix. There is no filename or extension restriction. `storageId` is issued by the attachment owner; a trusted local mapping to that store is required before I/O. It is not inferred from a path, package, or similarly named directory.
- `designated-file.path` is any exact user-selected pathname, including `goal.md`, a filename without an extension, or a file outside attachments. A relative path requires `baseDir`, captured from the established user-invocation base at designation time; that base must be an absolute directory after expansion. An absolute or `~/...` path omits `baseDir`. Never substitute the resumed process's working directory.
- `namespaceId`, `homeId`, and `pathStyle` bind explicit paths to the producer's filesystem and home. The consumer needs a trusted matching context; matching record strings alone is not proof. Normalize home paths as `~/...` at component boundaries. A foreign namespace/home is unresolved unless the user explicitly supplies a trusted relocation mapping. Display spelling alone is not portable identity.

After selection, the shared resolver separately checks existence, a regular non-symlink final file, and the managed locator's canonical containment. A deleted file yields `artifact-not-file`; a foreign store yields `artifact-location-unavailable`. Preserve the reference and the user's settled selection. Neither result authorizes recreating, relocating, restoring, or modifying the file. No content hash is required for a living goal merely to retain its identity.

## Presence and compatibility

Omitted `managedObjectiveArtifacts` means legacy/unknown association, not an empty list. Present `null` or a malformed record is invalid, not legacy absence. A new producer with no file selection emits `none` or `unavailable` explicitly. In version 1 the object is strict; new required semantics require a new version and a selected compatible consumer.

This is the native goal-tool/protocol contract. It does not silently redefine app-server schemas or other clients' null/omission conventions. Each adopted transport must expose a documented lossless mapping and compatibility profile. An optional field can still break an old strict decoder. A legacy projection must not overwrite or clear stored metadata it cannot represent.

## Specification cases

Evaluate a selected file plus historical/output records; deliberate no-file objectives; legacy absence versus present `null`; duplicate IDs and locators; two current roles; unsupported kinds; equal bytes in distinct role fixtures; arbitrary external and relative filenames; stale objective revisions; deleted files; and unmapped stores/homes. These are contract evaluations, not executed goal persistence or file restoration.
