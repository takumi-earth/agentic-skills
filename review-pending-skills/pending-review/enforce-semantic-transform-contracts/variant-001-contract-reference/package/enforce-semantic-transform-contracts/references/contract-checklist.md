# Semantic transformation contract checklist

Use this checklist before implementation and again during review. A checked row means the design answers the question; it does not prove the implementation.

## Identity and scope

- Give the transformation a stable ID and typed product owner.
- Define semantic identity independently from file path, line, spelling, or complete syntax.
- Declare the complete workspace, crate, module, or generated-content scope.
- State candidate cardinality and whether absence is optional or required.

## Discovery and drift

- Search the complete declared scope with the authoritative semantic query.
- Treat paths, markers, versions, hashes, fingerprints, and rendered fragments as hints only.
- Require every hint miss to continue with the authoritative query.
- Match only load-bearing semantic preconditions; wildcard unrelated syntax.
- Distinguish absent, ambiguous, mixed pre/post, and incompatible candidates.

## Rewrite and transaction

- Classify every candidate before changing any file.
- Refuse partial edits for ambiguity, incompatibility, or mixed state.
- Apply the smallest parsed-source change at dynamically discovered paths.
- Preserve all unrelated syntax and files.
- Verify the semantic postcondition inside the isolated transaction.
- Replay the transformation and require an empty semantic delta.
- Publish all authoritative changes atomically.

## Counterfactuals

The same transformation declaration must handle:

- trivia, formatting, and unrelated line shifts;
- item reorder and movement between permitted files or modules;
- unrelated fields, branches, statements, attributes, or helpers;
- an equal-looking decoy at the old path;
- two genuine semantic candidates;
- actual load-bearing drift;
- an already-applied workspace;
- irrelevant dependency or lockfile version changes.

## Exact ownership exception

Complete-body or byte equality is authoritative only when the repository explicitly owns the whole generated, vendored, protocol, or rendering artifact. Record that ownership decision and keep it out of adaptive upstream-source claims.
