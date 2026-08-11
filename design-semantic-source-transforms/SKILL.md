---
name: design-semantic-source-transforms
description: "Design, implement, or review parsed-source transformations whose targets must survive upstream formatting, line shifts, unrelated edits, and movement across files or modules. Use for AST, CST, HIR, or symbol-aware patch engines, codemods, fork adaptation, and migration jobs; especially when fixed paths, rendered fragments, token or body fingerprints, hashes, marker gates, or parser-bounded writes may be mistaken for semantic identity. Do not use solely to maintain an established exact generated or vendored output contract or to inventory regressions across checkpoints; use it when the ownership exception is disputed or mixed with adaptive transformations, and use `$audit-architectural-regressions` for checkpoint-wide source adjudication."
---

# Design Semantic Source Transforms

Preserve the smallest owned semantic delta while allowing upstream-owned source to evolve around it.

## Enforce the location-independent invariant

Require equivalent load-bearing semantic targets to produce the same applicability decision and semantic delta despite:

- formatting, comments, or line shifts;
- item reordering or unrelated syntax additions;
- movement between files or permitted modules;
- harmless spelling changes that resolve to the same symbol.

Reject these category substitutions:

- an AST-bounded write is not semantic target discovery;
- a trivia-insensitive token fingerprint or source-body hash is still a complete implementation snapshot;
- a field named `semantic_owner` is not a resolver or discovery mechanism;
- uniqueness inside one configured path is not uniqueness in the declared semantic scope;
- parsing a node and rendering it back to text does not make text matching structural.

Treat a known path, package version, textual marker, or import spelling as a non-authoritative hint only. A hint miss must continue with the full declared query and must never establish absence.

## Separate four responsibilities

Record each responsibility independently before implementation:

1. **Semantic identity:** name the program entity or operation that owns the change.
2. **Discovery scope:** name the crate, workspace, module family, or other complete permitted search boundary.
3. **Syntax anchor and rewrite:** identify the smallest concrete node that can be changed safely after discovery.
4. **Drift and postcondition:** state only the load-bearing precondition and the semantic state that must hold afterward.

Do not use exact equality of one complete upstream-owned item to perform all four jobs.

## Declare a typed transformation contract

Give every transformation a stable identity and typed contract equivalent to:

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

Use typed candidate and outcome states. Distinguish at least `PreState`, `PostState`, and `Incompatible` candidates, plus `Applied`, `AlreadyApplied`, optional absence, required absence, ambiguity, mixed-state conflict, incompatible shape, failed postcondition, and non-idempotent replay. Include discovered candidate identities and paths in diagnostic outcomes.

Read [the transformation contract](references/transformation-contract.md) before drafting or reviewing a transformation declaration, workspace discovery policy, ambiguity behavior, or full-item exception.

## Classify before mutating

Use this causal sequence:

```text
index the complete declared scope
    -> run the semantic query
    -> classify every candidate
    -> enforce cardinality and state compatibility
    -> plan the complete edit set
    -> apply the smallest edits to an isolated transaction
    -> re-index or refresh the transaction's semantic state
    -> verify the postcondition
    -> replay and require an empty semantic delta
    -> commit the verified transaction atomically
```

Do not write the first matching file while discovery is still incomplete. Zero candidates, multiple genuine candidates, mixed pre/post candidates, an unfamiliar load-bearing shape, a failed postcondition, or a non-idempotent replay must produce a typed outcome and leave the authoritative workspace byte-for-byte unchanged.

## Use the weakest sufficient semantic tier

Choose the least expensive tier that still proves identity:

1. Use typed syntax when the declaration or operation is unambiguous inside the complete scope.
2. Resolve symbols when aliases, imports, traits, receiver types, or method resolution make spelling insufficient.
3. Use a bounded token-tree fallback only inside one uniquely identified macro invocation when ordinary parsed syntax is unavailable.

Do not add a resolver dependency without the repository's dependency-review workflow and explicit authority. Stop if the required tier cannot be implemented faithfully with the authorized dependency surface.

## Keep the upstream seam small

- Capture and wildcard unrelated arguments, fields, bounds, statements, arms, attributes, and sibling items.
- Change only the load-bearing call, field, bound, expression, arm, signature part, or integration hook.
- Move substantial product behavior behind repository-owned functions, traits, callbacks, modules, or generated artifacts.
- Preserve workspace indexing, atomic edit transactions, changed-file ledgers, and replay machinery when they already satisfy the contract.
- Never translate a copied source body into a hash, normalized token list, regex, or other encoded snapshot and call it semantic.

Permit whole-item exactness only when the repository explicitly owns the entire generated, vendored, or emitted item and exact content is the declared contract. Label that ownership exception directly; do not advertise it as adaptive upstream patching.

Keep Git patches, three-way apply, and rename detection as import or conflict-evidence tools. Never let them silently become the correctness fallback after semantic discovery fails.

## Migrate a brittle patch engine in owner order

When the current engine already uses fixed paths, markers, complete fragments, or fingerprints:

1. Freeze new production callers of those mechanisms without weakening current behavior.
2. Inventory every transformation and broad helper caller by stable transformation ID, owner, scope, and current mechanism; do not stop at aggregate counts.
3. Add typed candidate states, outcomes, semantic deltas, and an isolated workspace transaction before translating individual callers.
4. Add authoritative workspace discovery and demote paths, markers, and versions to hints with full-query fallback.
5. Pilot one whole-item caller and one narrow expression, call, record, arm, or signature caller with movement and decoy evidence.
6. Port upstream-owned whole-item contracts first, then migrate exact fragment mechanisms owner by owner.
7. Move substantial product behavior behind repository-owned seams as each caller is narrowed.
8. Use `$verify-test-parity` and `$test-adaptive-source-transforms` before removing legacy tests or helpers.
9. Retire obsolete mechanisms only after production callers are gone, live behavior has equal-or-stronger evidence, and replay plus cross-version or synthetic-movement checks pass.

Do not translate complete source constants into another hash, token signature, template, or regex during migration. Preserve existing valid indexing, transaction, edit-ledger, and replay infrastructure rather than reimplementing it.

## Require behavior-first evidence

Use `$test-adaptive-source-transforms` for every adaptive transformation. Require movement, unrelated-extension, decoy, ambiguity, real-drift, recognized-post-state, replay, and dependency or lockfile variation with unchanged relevant source semantics before calling the transformation robust.

Treat existing path-local, full-body, fingerprint, or rendered-string tests as legacy evidence debt, not precedent. A user-selected semantic invariant governs the production mechanism and its tests even when the user did not enumerate every prohibited string API.

## Stop at ownership or identity gaps

Stop dependent implementation and report the exact missing decision when:

- two semantic owners plausibly qualify;
- the only proposed target identity is a path, marker, rendered fragment, or complete body;
- the rewrite appears to require local ownership of a complete upstream algorithm;
- mixed candidate states make an atomic outcome unclear;
- a new resolver or parser dependency needs approval;
- the exact-text exception is asserted without explicit whole-content ownership.

Use `$audit-architectural-regressions` instead when the primary deliverable is a complete checkpoint comparison, caller inventory, and per-site remediation disposition rather than one transformation's production contract.

Do not preserve a brittle mechanism behind a compatibility shim or automatic textual fallback.
