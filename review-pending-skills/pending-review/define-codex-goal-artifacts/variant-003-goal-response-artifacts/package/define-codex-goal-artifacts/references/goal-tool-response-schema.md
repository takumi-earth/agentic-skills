# Event-local goal response artifacts, version 1

This alternative adds `GoalToolResponse.managedObjectiveArtifacts` for one successful native goal-tool invocation. It leaves durable `ThreadGoal` artifact state unchanged. It does not promise a file association after resume or remove prose parsing unless the producer actually receives an independent authoritative designation.

## Exact response extension

The proposed `goal-response-artifacts/v1` profile uses this object when `goal` is non-null. An old response may omit the property; a version 1 response must explicitly report selection or unavailability. A response with `goal: null` omits it and has no artifact selection. Present `null`, duplicate JSON keys, unknown fields/tags, and malformed values are invalid, not legacy absence.

```typescript
type ResponseArtifactsV1 = {
  schemaVersion: 1;
  threadId: string;
  goalId: string;
  objectiveSha256: string;
  turnId: string;
  toolUseId: string;
  observedAtMs: number;
  selection:
    | { state: "selected"; artifactId: string; designation: Designation }
    | { state: "none" }
    | { state: "unavailable"; reason: "no-authoritative-input" };
  artifacts: Artifact[];
};
type Designation = {
  source: "user-path" | "managed-objective-input";
  inputId: string;
};
type Artifact = {
  artifactId: string;
  role: "current-objective" | "historical-input" | "output";
  locator:
    | { kind: "managed-file"; storageId: string; relativePath: string }
    | {
        kind: "designated-file";
        namespaceId: string;
        homeId: string;
        pathStyle: "posix" | "windows";
        path: string;
        baseDir?: string;
      };
};
```

All properties are required except `baseDir`. Identifiers are nonempty opaque strings; `schemaVersion` is integer `1` and `observedAtMs` is an integer Unix-millisecond timestamp in `0..=2^63-1`, neither Boolean. `objectiveSha256` is 64 lowercase hexadecimal characters over the exact returned objective's UTF-8 bytes, not the referenced file. Do not use timestamp recency as proof that a response is current.

Artifact IDs and normalized locators are unique. `selected` must name the sole `current-objective` record; `none` and `unavailable` prohibit such a record. Historical inputs and outputs may coexist but never supply a fallback current artifact. Unknown locator kinds or roles require a compatible new version, not silent filtering. Equal bytes in distinct files do not collapse their roles.

A managed locator is exactly `<uuid>/<filename>` in the attachment store identified by a trusted `storageId`: two nonempty slash-delimited components, UUID first, no traversal, NUL, backslash, or absolute prefix. Any filename/extension is allowed. A designated locator accepts any exact user-selected pathname, including outside attachments. A relative `path` requires an established absolute `baseDir` captured with that designation; absolute or `~/...` paths omit `baseDir`. No resumed working-directory guess is allowed.

Explicit paths resolve only in a trusted matching namespace, home, and pathname grammar. Normalize producer-home paths as `~/...` at component boundaries. A copied path does not identify another machine's file. Managed store IDs require a trusted local mapping; absent mappings and deleted files remain unresolved. The shared resolver separately checks regular-file identity and managed containment. Metadata does not authorize restoration or writes.

## Authoritative producer input

The producer receives a `GoalArtifactInput` from the trusted invocation context: the exact user path or selected managed attachment, its input identifier, established relative base when needed, and its association with the goal operation. This is a proposed internal input contract, not a new model-call argument currently accepted by Codex. The owner validates it against the actual user designation; a caller-supplied role/provenance label is insufficient.

Construct the response extension from that input and the same committed goal snapshot returned by the operation. Take the internal goal ID before the current protocol projection discards it. Take thread, turn, and tool-call identity from the invocation, not from arbitrary nested tool payload fields. Hash the objective from that returned snapshot; do not refetch state and combine a later hash with an earlier response.

If the invocation supplies no attributable artifact input, use `unavailable`. Use `none` only when the producer knows the objective deliberately selects no file. A status update does not itself provide a new designation, and it does not require asking the user again if the trusted invocation context already retains the applicable designation. This variant introduces no durable cache to recover an unavailable association.

Parsing objective prose at response construction is a legacy parsing adapter, not an independent typed authority source. It must preserve the existing exact-selection rules and report its provenance as legacy evidence outside this version 1 selected contract. It cannot fabricate `Designation` or silently claim that prose parsing was eliminated.

## Event binding and resume

Pass the extension unchanged as part of `PostToolUse.tool_response`. The consumer verifies its `threadId`, `turnId`, and `toolUseId` against the trusted live dispatch context, its goal ID against the goal snapshot associated with that call, and its objective hash against the exact returned objective. A transcript or copied JSON object can supply historical evidence but cannot self-authenticate as a live event.

For a current-goal action, also compare the response's goal ID and objective hash with the current authoritative goal observation supplied by the caller. If that observation is unavailable, report `current-goal-unverified`; do not infer authority from an old response's status or timestamp. A different current goal/objective yields `stale-goal-artifacts`. An event with mismatched invocation identity yields `artifact-event-mismatch`. The adapter does not automatically query or mutate goal state to obtain missing authority.

An exactly replayed event remains evidence of the original operation. This metadata does not provide an exactly-once effect guarantee or authorize a new replay ledger. Apply the existing workflow's replay/idempotence contract when an effect is separately authorized.

After resume without the earlier response or a fresh attributable invocation input, the association is unavailable. Do not scan historical responses to choose a current artifact. A fresh `get_goal` or status response may emit `unavailable`; that is an explicit limit of this event-local alternative. A durable association would require selecting the sibling durable-state design, not adding hidden persistence here.

## Compatibility and specification cases

Keeping `ThreadGoal` unchanged does not preserve compatibility automatically: the containing `GoalToolResponse` gains a field. Select the new response profile only for compatible consumers; legacy strict readers need an explicit projection that omits the extension. Version 1 readers reject invalid metadata instead of falling back. `PostToolUse` must preserve the structured value rather than render and reparse it as human text.

Evaluate create/get/update with and without authoritative input; a null goal; malformed or missing versioned metadata; exact and mismatched call identity; a replacement goal; objective changes with the same goal ID; replayed events; resume without prior metadata; external and relative user paths; unknown kinds; deleted files; and strict old response decoders. These are specification cases, not executed Codex or live-hook evidence.
