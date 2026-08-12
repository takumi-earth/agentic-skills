# Metamorphic and mutation matrix

Use this matrix to prove that an adaptive transformation observes semantic ownership instead of current rendered source.

Treat the matrix as a coverage model, not a demand for a separate handwritten fixture and test for every cell. Apply shared engine invariants once through a reusable family harness, then require each transformation to supply the semantic owner, load-bearing precondition, rewrite, and postcondition that the harness varies.

## Contents

1. Required variation matrix
2. Candidate and outcome polarities
3. Wrong-owner mutation tests
4. Typed assertion examples
5. Product-owner evidence
6. Exact-text exceptions
7. Review checklist

## Required variation matrix

Apply each relevant variation without changing the transformation declaration or the test oracle:

Determine relevance from the declared production scope and semantic contract, never from current fixture convenience or a path-bound implementation. Movement within scope, unrelated extension, decoys, ambiguity, drift, recognized post-state, and replay cannot be waived because the current mechanism cannot handle them.

| Variation | Required observation |
| --- | --- |
| Blank lines, comments, whitespace, or formatter changes | Same semantic candidate and semantic delta |
| Unrelated lines inserted before the target | Same result and no positional dependency |
| Functions or items reordered | Same result |
| Target moved from file `A` to file `B` inside scope | Target discovered at `B`; only reported path changes |
| Target moved between permitted modules | Same semantic transformation |
| Unrelated field, branch, attribute, bound, parameter, helper, assertion, or method added | Added syntax preserved; applicability unchanged |
| Equal-looking call in another function, macro, comment, string, or test | Only the semantically owned occurrence changes |
| Near match remains at the old path while the true target moves | True target selected; path-local decoy untouched |
| Import alias or equivalent spelling changes | Same result when resolved identity is unchanged |
| Dependency or lockfile version changes while relevant source semantics do not | Same applicability and delta |

Generate variants from one minimal fixture model where practical. Do not store a complete before/after source snapshot for every row.

## Candidate and outcome polarities

Test these outcomes independently:

| Candidate state | Required outcome | Mutation allowance |
| --- | --- | --- |
| One valid pre-state candidate | `Applied` with one declared semantic delta | Planned edit set only |
| One recognized post-state candidate | `AlreadyApplied` | Zero edits |
| No optional candidate | Optional absence | Zero edits |
| No required candidate | Required absence with query evidence | Zero edits |
| Two genuine candidates | Ambiguity with both identities | Zero edits |
| One candidate with changed load-bearing shape | Incompatible shape with failed predicate | Zero edits |
| Mixed pre-state and post-state candidates when contract forbids the mix | Typed conflict or ambiguity | Zero edits |
| Replay after successful apply | Already applied or empty delta | Zero edits |

Assert that every non-applying outcome preserves the complete virtual workspace, not merely the originally hinted file.

## Wrong-owner mutation tests

Build at least one fixture containing:

- the intended semantic owner;
- an unrelated owner with an equal-looking child node;
- a path-local near match or marker-bearing decoy;
- optional appearances in comments, strings, macro tokens, or test code.

First prove that only the intended node changes. Then mutate the fixture so the old and new-looking nodes trade owners. The oracle must fail if the transformation edits the wrong owner.

Avoid global assertions such as “one old call and one new call remain.” That multiset can be correct while ownership is reversed.

## Typed assertion examples

Prefer assertions over semantic queries and captured nodes:

```rust
let result = apply_transform(workspace, transform_id)?;
assert_eq!(result.outcome.kind(), OutcomeKind::Applied);
assert_eq!(result.delta.operations(), [expected_operation]);

let target = result.syntax.find_function(target_symbol)?;
assert_eq!(target.resolved_calls(expected_callee).len(), 1);
assert_eq!(target.required_argument(expected_callee), expected_argument);

let decoy = result.syntax.find_function(decoy_symbol)?;
assert_eq!(decoy.resolved_calls(expected_callee), before_decoy_calls);
assert_eq!(decoy.relevant_control_flow(), before_decoy_control_flow);
assert_eq!(result.changed_files, [moved_target_path]);
```

For records, arms, and signatures, query the intended owner and compare only relevant typed fields plus explicitly selected preserved children. For diagnostics, compare the error variant, stable code, candidate identities, paths, cardinality, and failed predicate.

## Product-owner evidence

Map each claimed preserved capability to an executable observation:

| Claimed capability | Acceptable evidence | Inadequate marker |
| --- | --- | --- |
| Streaming | Real chunk flow, ordering, backpressure, or termination | `preserve_streaming()` remains in source |
| Cancellation | Cancellation signal reaches the owner and stops effects | `cancellation_is_preserved()` string appears |
| Authentication or OAuth | Credential/token flow and failure behavior | Helper name survives rendering |
| Schema | Produced typed schema properties or consumer behavior | Copied adapter body equals expectation |
| Lifecycle | Actual state transitions and cleanup order | Marker call or comment |
| Diagnostics | Typed code, fields, and causal context | Complete English text unless public API |

Keep transformation wiring tests small. Put substantive behavior tests at the module, crate, service, or protocol owner that implements the capability.

## Exact-text exceptions

An exact text assertion is legitimate only when all of these are true:

1. The text or bytes are themselves the documented external or owned generation contract.
2. The test is named and located as a rendering, wire, CLI, diagnostic-wording, or generation contract.
3. The exact expectation is not being used to infer semantic target discovery or preservation.
4. A change to irrelevant upstream syntax cannot fail the test.

Examples include a protocol field, documented CLI line, stable diagnostic code, exact generated bytes, or fully repository-owned generated source. A complete rendered upstream function is not an exception merely because the parser produced it.

## Review checklist

- Structural helpers return typed results rather than raw strings.
- No structural assertion calls substring, regex, prefix, suffix, snapshot, or raw equality on transformed source.
- No selected parsed node is immediately rendered to launder the oracle.
- Primitive fixtures are minimal and version-neutral.
- Full upstream bodies are not copied into fixtures or expectations.
- Every movement and irrelevant-extension variation reuses the same transform and oracle.
- Decoys and wrong-owner swaps can make the suite fail.
- Ambiguity, incompatibility, post-state, and replay have typed assertions and zero-edit checks.
- Claimed product behavior is executed at its real owner.
- Legitimate exact-text contracts are isolated and explicitly named.
- Unexecuted tests are not reported as passing evidence.
- Touched legacy contracts map to executed typed or owner-level evidence.
- `$verify-test-parity` runs only when comprehensive removed-test accounting is explicitly selected; unresolved local parity risk is reported for a user decision rather than automatically escalating the workflow.
