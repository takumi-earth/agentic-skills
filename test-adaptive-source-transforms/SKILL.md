---
name: test-adaptive-source-transforms
description: "Design, implement, or review behavior-first tests for adaptive parsed-source transformations and codemods. Use when production promises semantic or location-independent targeting; when structural tests expose rendered source or use substring, regex, snapshot, raw equality, copied upstream bodies, or parse-then-text assertions; or when a green test could mutate the wrong owner. Do not use solely for a documented exact-text or byte contract independent of parsed-source discovery."
---

# Test Adaptive Source Transforms

Prove the semantic relationship the transformation promises. Never use rendered parsed source as a proxy for structural correctness.

## Remove invalid assertion surfaces first

When rendered-source assertions have been rejected, remove the reusable escape hatches before rewriting individual tests:

- raw transformed-source return values;
- `Deref<Target = str>`, `AsRef<str>`, assertion-oriented `Display`, and `rendered_source()`;
- structural `expected_contains`, `expected_absent`, snapshot, regex, and occurrence-count helpers;
- unrestricted parser nodes or token streams that can be rendered and laundered into a string oracle.

Let resulting compile failures identify tests that need typed replacements. Do not keep a deprecated raw-string helper during migration, and do not replace it with a wrapper around the same rendered data.

Small Rust strings remain valid parser inputs. The prohibition applies to correctness evidence derived from transformed output.

## Choose the real evidence owner

Use only the layers required by the behavior under test:

1. **Engine or family tests:** prove shared query, classification, atomicity, and metamorphic behavior once for reusable primitives.
2. **Transformation tests:** prove the registered ID, semantic owner, scope, typed captures, minimal delta, preservation, outcome, and discovered path.
3. **Product-owner tests:** exercise substantive authentication, streaming, cancellation, schema, lifecycle, protocol, or service behavior at its real owner.
4. **Rendering-contract tests:** assert exact text only when text or bytes are the documented external or repository-owned contract.

Do not manufacture all four layers for every caller. A small wiring transformation needs typed wiring evidence; substantive product behavior belongs in its owner; shared engine invariants belong in a shared family harness.

## Make typed assertions the easiest path

Return a typed structural result equivalent to:

```rust
struct AppliedSourceTransformation {
    outcome: TransformationOutcome,
    syntax: ParsedWorkspace,
    delta: SemanticDelta,
    changed_files: Vec<WorkspacePath>,
}
```

Keep `ParsedWorkspace` opaque. Provide typed queries for declarations, implementations, calls, arguments, fields, arms, paths, owners, candidates, failed predicates, and semantic deltas.

Assert that:

- the intended semantic owner was selected;
- only the load-bearing child changed;
- equal-looking wrong-owner nodes remained unchanged;
- unrelated syntax was preserved;
- cardinality and typed outcome are correct;
- reported paths follow the discovered target;
- replay has an empty semantic delta.

An exact count over typed candidates in the selected owner is valid when cardinality is the contract. A count over rendered text is not. Byte-for-byte workspace equality is valid for proving that a rejecting outcome made zero edits.

## Apply the adaptive matrix proportionally

Read [the metamorphic and mutation matrix](references/metamorphic-matrix.md) when adding a transformation family, porting a brittle caller, or reviewing broad adaptive coverage.

Cover the applicable invariants through reusable fixture mutation or a shared family harness:

- trivia, formatting, line shifts, and item reordering;
- file or permitted-module movement;
- unrelated structural extension;
- equal-looking decoys and stale path-local near matches;
- two genuine candidates and mixed candidate states;
- real load-bearing drift;
- unchanged source semantics across dependency or lockfile changes;
- recognized post-state and replay.

Do not create a separate full-source fixture and expected body for every matrix cell. Vary the workspace while keeping the transformation declaration and typed oracle unchanged.

Use the target/decoy swap mutation: exchange which owner contains the old and new-looking operation. The test must fail if selection follows shape rather than ownership.

## Prove actual product behavior

Do not use marker functions or invented calls whose names claim that streaming, cancellation, authentication, OAuth, schema, or lifecycle behavior survived. Exercise the real effect, failure order, cancellation path, emitted protocol value, or typed state transition.

When a transform only wires a Bun-owned hook or another repository-owned seam, keep the transformation test small and test substantive behavior through that owner.

## Harden by construction

- Keep rendering inside parser, edit, and diagnostic adapters.
- Use API visibility or compile-fail tests to keep structural results away from raw-string assertions.
- Use type-aware or dataflow-aware enforcement only when the type boundary cannot make misuse impossible.
- Do not add a repository-wide grep for string methods.
- Treat large fixture overlap with upstream source as a review signal, never as transformation authority.
- Compare typed diagnostic codes and fields; compare English wording only when it is public API.

## Replace touched tests without an upfront audit

For each test broken by removal of a legacy assertion surface:

1. Define the current semantic or product contract first.
2. Add typed or owner-level evidence for that contract.
3. Consult the old test through Git only if it may contain an additional observable behavior.
4. Map each still-live positive, negative, preservation, ordering, idempotence, cleanup, or side-effect assertion to executed replacement evidence.
5. Remove the invalid textual oracle.

Keep this mapping inline or in the existing task record unless a broad audit was explicitly requested. Use `$verify-test-parity` only when the user explicitly requests comprehensive removed-test accounting. If local mappings cannot determine whether a live behavior was lost, identify that contract and ask before starting the audit.

Do not retire behavior merely because its old oracle was brittle, and do not invent replacement behavior to close bookkeeping.

## Stop on an unprovable oracle

Stop dependent work only when:

- target and decoy ownership cannot be distinguished through typed queries;
- the product behavior has no executable owner-level observation;
- the only possible fixture copies a complete upstream implementation; or
- an exact-text exception lacks a documented external or owned-output contract.

Do not weaken the transformation promise to fit an easy fixture.
