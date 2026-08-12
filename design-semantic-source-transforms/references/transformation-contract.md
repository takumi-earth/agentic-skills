# Semantic transformation contract

Use this reference to specify or review one adaptive parsed-source transformation.

## Contents

1. Equivalence invariant
2. Migration from brittle mechanisms
3. Required declaration fields
4. Candidate classification and atomicity
5. Semantic identity, syntax anchoring, and drift examples
6. Discovery hints and movement
7. Ownership and exact-content exceptions
8. Acceptance checklist

## Equivalence invariant

Define `relevant_semantics(workspace, transform)` as the load-bearing facts consumed by the transformation. For workspaces `A` and `B`:

```text
relevant_semantics(A, T) == relevant_semantics(B, T)
    => applicability(A, T) == applicability(B, T)
    => semantic_delta(A, T) == semantic_delta(B, T)
```

File paths, line numbers, trivia, item order, unrelated sibling syntax, package version strings, and complete upstream-owned bodies must not appear in `relevant_semantics` unless the user explicitly made one of them part of the external contract.

## Migration from brittle mechanisms

When fixed paths, complete bodies, fingerprints, exact fragments, marker gates, or rendered-source test helpers have been explicitly rejected, remove their reusable APIs first. Do not keep them live while designing replacements, and do not encode them as hashes, regexes, token signatures, templates, or compatibility fallbacks.

Temporary compile failures are the migration queue. Rebuild each affected capability through the typed contract below. Define the current semantic identity and product delta before consulting old source. Use `git show` or `git grep` against a known pre-removal ref only when one specific caller or test needs historical context.

Do not require a global inventory or audit before implementation unless that inventory is itself the requested deliverable. Compiler coverage across the repository's real feature and target surface, followed by the removal of all legacy API definitions, is stronger completion evidence than an aggregate textual count.

## Required declaration fields

Record these fields for every transformation:

| Field | Required meaning | Invalid substitute |
| --- | --- | --- |
| `id` | Stable transformation identity | Current source path or line |
| `owner` | Typed product or integration owner | Diagnostic string with no resolution behavior |
| `scope` | Complete permitted semantic search boundary | One expected file |
| `query` | Candidate identity independent of location | Rendered substring or full token signature |
| `precondition` | Load-bearing facts required by the rewrite | Equality of the complete item |
| `rewrite` | Smallest owned syntax mutation | Copied replacement body |
| `postcondition` | Semantic state after success | Expected rendered fragment appears |
| `cardinality` | Permitted candidate count and state combination | First match wins |

Also record any path or marker hints, their miss behavior, and the authoritative fallback query.

## Candidate classification and atomicity

Classify the complete candidate set before creating a write plan:

```rust
enum CandidateState {
    PreState(RelevantCaptures),
    PostState(PostconditionEvidence),
    Incompatible(FailedPredicate),
}

enum TransformationOutcome {
    Applied { files: Vec<WorkspacePath>, delta: SemanticDelta },
    AlreadyApplied { files: Vec<WorkspacePath> },
    OptionalTargetAbsent,
    RequiredTargetAbsent { query: QueryDescription },
    Ambiguous { candidates: Vec<CandidateIdentity> },
    StateConflict {
        pre: Vec<CandidateIdentity>,
        post: Vec<CandidateIdentity>,
    },
    IncompatibleShape {
        candidate: CandidateIdentity,
        failed: PredicateId,
    },
    PostconditionFailed { failed: PredicateId },
    ReplayNotIdempotent { delta: SemanticDelta },
}
```

Names may differ, but these meanings must stay distinct. Never collapse required absence, optional absence, ambiguity, mixed pre/post state, unfamiliar drift, failed postcondition, non-idempotent replay, and recognized post-state into one `false` or `None` result.

Plan all edits only after candidate cardinality and state compatibility pass. Apply the plan to an isolated virtual transaction, refresh that transaction's semantic state, verify the postcondition, and replay the transformation there. Commit authoritative bytes atomically only after both checks pass. A candidate, postcondition, or replay failure must return its typed outcome and leave the authoritative workspace byte-for-byte unchanged.

## Semantic identity, syntax anchoring, and drift examples

### Trait implementation

- Semantic identity: implementation of the resolved trait for the resolved type.
- Syntax anchor: the selected method, bound, or schema-construction expression.
- Drift predicate: only the method or expression facts required for the delta.
- Invalid shortcut: exact tokens of the complete `impl` block.

### Function call

- Semantic identity: resolved callee inside the resolved owning function or operation.
- Syntax anchor: the one call expression and semantically relevant argument.
- Drift predicate: required argument relationship or missing wrapper.
- Invalid shortcut: matching the rendered call everywhere or counting old and new strings globally.

### Record literal

- Semantic identity: resolved record type in the intended owner.
- Syntax anchor: the required field or insertion point.
- Drift predicate: required field absent or in the pre-state.
- Invalid shortcut: equality of the complete record expression.

### Match arm

- Semantic identity: load-bearing pattern and captured bindings inside the intended operation.
- Syntax anchor: the relevant arm subexpression.
- Drift predicate: the old subexpression relationship.
- Invalid shortcut: copied match body or positional arm index.

### Arbitrary macro tokens

- Semantic identity: one uniquely identified macro invocation in the complete scope.
- Syntax anchor: a bounded token-tree region with explicit captures.
- Drift predicate: only the token relationship needed by the rewrite.
- Invalid shortcut: unscoped regex or token replacement across files.

## Discovery hints and movement

A path or marker hint is lawful only when all of these are true:

1. It can accelerate candidate discovery without changing the query result.
2. Its miss continues with the complete semantic query.
3. A stale decoy at the hinted path cannot win over the true semantic candidate elsewhere.
4. Full-scope cardinality is checked before mutation.
5. The outcome and edit ledger report the discovered path, not the configured hint.

Prove movement with a virtual workspace containing an old path, a new path, and a near-match decoy. Move the true target without changing the transformation declaration. The result must change only the discovered output path.

## Ownership and exact-content exceptions

Move substantial product behavior out of upstream-owned implementations. Prefer a small call, hook, callback, trait method, configuration field, or generated registration seam whose upstream mutation remains narrow.

Whole-item replacement is allowed only when all of these are explicit:

- the repository owns the entire item rather than a delta inside upstream code;
- exact emitted content is the contract;
- regeneration or vendoring is the named mutator;
- tests assert that owned output contract directly;
- the mechanism is not described as location-independent semantic patching.

If any condition is missing, decompose the item into semantic query, minimal rewrite, and postcondition.

## Acceptance checklist

- Obsolete generic APIs and structural-test escape hatches are unavailable from the start of migration.
- No compatibility wrapper, hash, regex, token signature, template, or Git fallback recreates them.
- The target can move between permitted files or modules without declaration changes.
- Formatting, comments, line shifts, item order, and unrelated syntax do not affect applicability.
- Equal-looking decoys in other owners, comments, strings, macros, and tests remain untouched.
- Two genuine candidates return typed ambiguity with zero edits.
- Mixed pre/post candidates return typed state conflict with zero authoritative edits.
- Real load-bearing drift returns typed incompatibility with zero edits.
- Recognized post-state returns `AlreadyApplied` or its typed equivalent.
- Replay produces no semantic delta.
- A failed postcondition leaves the authoritative workspace byte-for-byte unchanged.
- A non-idempotent replay leaves the authoritative workspace byte-for-byte unchanged.
- The isolated transaction is published only after postcondition and replay checks pass.
- The edit ledger names dynamically discovered paths and typed ownership.
- No complete upstream-owned body, fingerprint, hash, or fixed path defines semantic identity.
- Marker misses cannot suppress the authoritative query.
- Dependency, lockfile, or package-version drift with unchanged relevant source semantics leaves applicability and semantic delta unchanged.
- A resolver dependency, compatibility layer, or Git fallback was not added without explicit authority.
- `$test-adaptive-source-transforms` proves the same invariant through typed evidence.
