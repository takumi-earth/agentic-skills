# Staged object contract

Load this reference when creating, verifying, or completing a `variant-004-write-ahead-single-invocation-commit` batch.

## Index authority

After validation and caller-owned staging, record the complete index tree for every declared candidate root. For each stage-zero blob, preserve:

- the repository-relative pathname;
- the Git mode;
- the Git object identifier;
- a SHA-256 digest of the blob bytes;
- the hex-encoded symlink-target bytes when the mode is `120000`.

Reject unmerged stages, unsupported object modes, roots without staged transition coverage, unrelated staged paths, and candidate roots with untracked or unstaged remainder.

## Transition authority

Require `HEAD` to equal the manifest's `precommit_oid` through `verify-precommit`. After the caller commits, require exactly one transition from that OID, require every declared root and no unrelated path in the transition, and require the resulting commit's tree entries to equal the manifest snapshot.

## Mutation boundary

The helper may create an exclusive immutable manifest and append one result record. It may inspect Git, the selected evidence files, and the declared candidate roots. It may not mutate the index, create a commit, edit a candidate, or rewrite an existing manifest or result.
