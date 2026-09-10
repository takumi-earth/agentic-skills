# Typed artifact consumer contract

This inert alternative consumes one explicitly selected producer profile. The paired producer specifications were corrected in `516fe93`; the pairing does not adopt either protocol or make the current runtime emit its fields.

| Selected profile | Exact metadata location | Binding required before selection |
| --- | --- | --- |
| `durable-goal-artifacts/v1` | `tool_response.goal.managedObjectiveArtifacts` or the same field in an authoritative current goal snapshot | `schemaVersion: 1`, exact `threadId`, `goalId`, `objectiveRevision`, and `objectiveSha256`. |
| `goal-response-artifacts/v1` | `tool_response.managedObjectiveArtifacts` | `schemaVersion: 1`, exact goal/objective binding plus `turnId` and `toolUseId` from the trusted live invocation. `observedAtMs` is an observation timestamp, not a freshness oracle. |

Read the selected [durable producer schema](../../../../../define-codex-goal-artifacts/variant-002-thread-goal-artifacts/package/define-codex-goal-artifacts/references/thread-goal-artifact-schema.md) or [response-only producer schema](../../../../../define-codex-goal-artifacts/variant-003-goal-response-artifacts/package/define-codex-goal-artifacts/references/goal-tool-response-schema.md) before applying its field contract. Both use strict objects, required fields, unique IDs, tagged locators, nonempty identity strings, integer versions rather than Booleans, and distinct absence/invalid outcomes. A number named `schemaVersion` alone does not choose the producer model.

The caller supplies the supported profile and the current authoritative goal observation through the trusted task/dispatch context. Compare the metadata with those inputs; do not let the metadata authenticate itself. The current observation must include the selected profile's identity fields. Missing authority yields `current-goal-unverified`; the resolver does not automatically execute a goal query, infer identity from a title, or select a transcript response. For response-only metadata, also require the exact live event binding; copied or replayed JSON is historical evidence unless the existing workflow separately establishes its current applicability.

## Validation and selection order

1. Validate the selected profile, supported record shape, and complete metadata before filesystem access. Both producer fields present yields `ambiguous-artifact-producer`, even if they happen to agree; do not merge lifetimes or pick by array/location order. A future explicit projection may select one before invoking this consumer.
2. Preserve absence distinctions. A missing field under a declared legacy profile is `legacy-artifacts-absent`. A missing required version 1 field is `missing-artifact-metadata`. Present `null`, malformed nested data, duplicate keys/IDs, or impossible selection is `invalid-artifact-metadata`. Unknown version, role, or locator kind is `unsupported-artifact-metadata`. None of these invalid/unsupported results licenses a prose fallback.
3. Verify goal/event bindings against the supplied authority. A different goal, objective revision, or objective hash is `stale-goal-artifacts`; a different live call is `artifact-event-mismatch`. Successful transport or an old `complete` status is not current authority.
4. Interpret `selection` separately from the array. `none` means no selected file; `unavailable` means the producer lacks attributable selection information. Neither becomes the sole historical/output file. `selected` must name exactly one record and that record must be the only `current-objective` role. The designation's `source` and `inputId` must be verified by the trusted producer against actual user input; a role label or assistant-authored provenance cannot replace it.
5. Reject duplicate normalized locators before using them as distinct candidates. Different files with matching bytes remain distinct roles. Do not discard unsupported records or duplicates to manufacture cardinality one.
6. Resolve only the selected locator through the shared pure owner, retaining source attribution and the selected object's identity. Observe file availability separately from the user's settled decision.

## Locator and filesystem boundary

A `managed-file` locator has a trusted `storageId` plus `<uuid>/<filename>` relative to that mapped attachment store. Require exactly two nonempty slash-delimited components, a UUID first component, no traversal/NUL/backslash/absolute prefix, canonical containment, and a regular non-symlink final file. Validate the runtime/store mapping independently; do not search every store or derive a root from the package path. The filename and extension are unrestricted.

A `designated-file` locator has the exact user path, trusted namespace/home/path grammar, and an established absolute `baseDir` only when the path is relative. It can name any file, including outside attachments, a bare filename, or a file without an extension. Use the shared `resolve_designated_artifact` boundary, not managed-layout checks. The caller must have selected this mode from actual user designation before resolution; a failed managed lookup cannot be relabeled as explicit authority.

Home paths render as `~/...` at component boundaries, using the bound producer home. Preserve sibling-prefix paths and unrelated strings. A foreign home, namespace, store, or pathname grammar is unresolved without a trusted mapping; never expand using an accidental local home or resumed working directory. Missing/non-regular files preserve `artifact-not-file`; containment failures preserve the managed resolver's failure. File absence does not erase the reference or authorize restore, relocation, enumeration, writes, or goal completion.

## Current owner and output

The selected typed adapter belongs to `maintain-living-goal/scripts/goal_artifact_resolution.py`. Its current `GoalArtifactResolution` object carries status, stage, code, condition, expected, received, candidate count, artifact, and approach. Preserve that result shape and diagnostic facts; add the typed selection boundary there if this alternative is later implemented. `maintain-living-goal/scripts/goal_completion_handoff_hook.py` and `auto-skill-enhancer/scripts/post_goal_review_hook.py` remain consumers, with their existing hook envelopes and empty-stderr policies.

Those three files were read through EOF at `~/agentic-skills` revision `c761c38`. Their current implementation supports exact designated paths and legacy objective/environment resolution; it does not implement the proposed typed producer profiles. The source observation is separate from adopting or executing this consumer.
