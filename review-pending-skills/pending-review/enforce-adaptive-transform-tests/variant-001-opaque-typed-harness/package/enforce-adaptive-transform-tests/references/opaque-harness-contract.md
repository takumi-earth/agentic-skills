# Opaque structural-test harness contract

## Public result surface

Expose only typed facts needed by structural tests:

```text
AppliedTransformation
  outcome: TransformationOutcome
  candidates: CandidateSet
  selected_owner: SemanticOwner
  delta: SemanticDelta
  changed_paths: WorkspacePaths
  workspace: StructuralWorkspace
  replay: ReplayOutcome
```

Provide typed queries for functions, implementations, calls, arguments, fields, arms, attributes, owners, and unchanged siblings. Return opaque identities or comparison handles for preserved nodes.

## Forbidden escape hatches

The structural result and its children must not expose:

- raw source, rendered syntax, token streams, serialization, or unrestricted parser nodes;
- `Display`, source-bearing `Debug`, `Deref<Target = str>`, or `AsRef<str>`;
- arbitrary `text()`, `render()`, `to_source()`, or snapshot helpers;
- global substring or occurrence-count assertions.

Keep parsing and rendering internal to the harness. Diagnostics may expose stable codes, typed fields, candidate identities, and bounded source locations without becoming the correctness oracle.

## Required API-shape checks

- Prove structural results cannot be passed to string APIs without an explicit forbidden conversion.
- Prove equal-looking nodes in different owners retain distinct identities.
- Prove ambiguity and incompatibility return no mutable workspace handle.
- Prove replay exposes an empty semantic delta.

## Exact-output boundary

When emitted text or bytes are themselves the documented contract, use a separate `RenderedContractResult` owned by that output suite. Do not add a rendering escape hatch to the structural type.
