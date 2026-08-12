---
name: design-semantic-source-transforms
description: "Design, implement, or review parsed-source transformations whose targets must survive formatting, line shifts, unrelated edits, and movement across files or modules. Use for AST, CST, HIR, or symbol-aware patch engines, codemods, fork adaptation, and migration jobs; especially when fixed paths, rendered fragments, body fingerprints, hashes, marker gates, or parser-bounded writes are being mistaken for semantic identity. Do not use for an established exact generated or vendored output contract or for a checkpoint-wide regression inventory."
---

# Design Semantic Source Transforms

Preserve the smallest owned semantic delta while upstream-owned source evolves around it.

## Remove obsolete mechanisms first

When the user has rejected fixed-path, complete-body, fingerprint, exact-fragment, marker-gated, or rendered-source patching, make those mechanisms unavailable before using nearby code as precedent:

1. Remove the generic legacy production APIs and structural-test escape hatches.
2. Do not retain deprecated aliases, compatibility wrappers, hashes, token signatures, regexes, or automatic textual fallbacks.
3. Let compile failures identify live capabilities that need semantic replacements.
4. Rebuild each capability end to end through the typed contract in this skill.
5. Consult Git history only when one specific deleted caller or test may contain additional behavior; define the current semantic contract first.

Do not require an upfront caller inventory, rollout reconstruction, selected parity baseline, or aggregate count before implementation unless the user explicitly requested that audit as a deliverable. A temporary compile-red migration state is preferable to keeping an invalid reusable mechanism alive.

If exact whole-source behavior is legitimate for repository-owned generated or vendored content, provide a separately named ownership-specific API. Do not preserve a generic whole-item mechanism that upstream-owned transformations can call.

## Enforce location-independent identity

Require equivalent load-bearing semantic targets to produce the same applicability decision and semantic delta despite:

- formatting, comments, line shifts, or item reordering;
- unrelated fields, arguments, branches, attributes, helpers, or instrumentation;
- movement between permitted files or modules;
- harmless spelling changes that resolve to the same symbol;
- dependency or lockfile changes when the relevant source semantics are unchanged.

Reject these substitutions:

- an AST-bounded write is not semantic discovery;
- a trivia-insensitive fingerprint is still a complete implementation snapshot;
- uniqueness in one configured path is not uniqueness in the declared semantic scope;
- a diagnostic owner label is not symbol or owner resolution;
- parse-then-render matching is still text matching.

Treat a known path, marker, version, or import spelling as a non-authoritative hint only. A hint miss must continue with the full query, and full-scope cardinality must still run.

## Declare the typed contract

Keep these responsibilities independent:

```rust
Transformation {
    id: TransformId,
    owner: TransformOwner,
    scope: SemanticScope,
    query: SemanticQuery,
    precondition: RelevantStructuralPredicate,
    rewrite: MinimalSyntaxRewrite,
    postcondition: SemanticPostcondition,
    cardinality: Cardinality,
}
```

Distinguish `PreState`, `PostState`, and `Incompatible` candidates. Return distinct typed outcomes for application, recognized post-state, optional or required absence, ambiguity, mixed-state conflict, incompatible shape, failed postcondition, and non-idempotent replay. Include discovered identities and paths in results.

Read [the transformation contract](references/transformation-contract.md) when implementing a declaration, workspace query, ambiguity behavior, or exact-content exception.

## Classify before mutating

Use this production sequence:

```text
index the complete declared scope
    -> query and classify every candidate
    -> enforce cardinality and state compatibility
    -> plan and validate the complete edit set
    -> apply minimal edits to an isolated transaction
    -> refresh semantic state
    -> verify the postcondition
    -> replay and require an empty semantic delta
    -> publish the verified transaction atomically
```

Discovery, ambiguity, mixed state, drift, postcondition failure, and replay failure must leave the authoritative workspace unchanged.

## Use the weakest sufficient semantic tier

1. Use typed syntax when identity is unambiguous across the complete scope.
2. Resolve symbols when aliases, imports, traits, receiver types, or method resolution affect identity.
3. Use a bounded token-tree query only inside one uniquely identified macro invocation.

Stop only if the necessary tier requires an unauthorized dependency or an unresolved semantic owner. Do not fall back to a complete body, path, marker, or Git patch.

## Keep the upstream seam small

- Capture and wildcard unrelated syntax.
- Change only the load-bearing call, field, bound, expression, arm, signature part, or hook.
- Move substantial product behavior behind repository-owned functions, traits, callbacks, adapters, or services.
- Reuse valid indexing, transaction, ledger, and replay infrastructure.
- Report actual discovered paths rather than configured historical paths.

Permit whole-item exactness only when the repository owns the complete output and exact bytes or source are the declared contract. Keep that ownership exception outside the adaptive transformation API.

## Migrate in vertical slices

For each compile failure caused by legacy API removal:

1. State the intended product delta in one sentence.
2. Define the owner, complete scope, query, minimal precondition, rewrite, postcondition, and cardinality.
3. Implement the production declaration and smallest edit.
4. Add typed movement, unrelated-extension, decoy, ambiguity, drift, post-state, and replay evidence through `$test-adaptive-source-transforms`.
5. Add product-owner behavior evidence when the transform wires substantive behavior.
6. Finish the slice before moving to the next caller.

Pilot one former whole-item caller and one narrow expression, call, record, arm, or signature caller, then reuse the resulting primitives. Do not create a separate late cleanup phase: the old API was removed at the start, and each capability returns only through the semantic interface.

Use `$verify-test-parity` only when the user explicitly requests comprehensive removed-test accounting. If local touched-test mappings cannot establish whether live behavior was lost, report the unresolved contract and ask before starting that audit.

## Stop at real design gaps

Stop dependent implementation only when:

- two semantic owners plausibly qualify;
- symbol resolution needs a new dependency;
- the smallest safe seam still requires ownership of an entire upstream algorithm;
- mixed candidate states lack a defensible atomic outcome; or
- an exact-content exception lacks explicit whole-content ownership.

Do not stop for a missing historical count, a deleted snapshot helper, or the absence of an upfront inventory.
