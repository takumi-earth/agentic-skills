---
name: review-strict-dependency-candidates
description: "Research and present third-party crate or runtime dependency candidates before adoption in the `strict*` ecosystem. Use when evaluating, comparing, adding, replacing, or rejecting a crate, fork, platform binding, process library, or tool dependency, and when candidate facts must survive compaction without repeated research."
---

# Review Strict Dependency Candidates

Separate research authority from adoption authority. Maintain a durable candidate ledger, present a complete comparison, block the goal, and wait for explicit user selection before production manifest or lockfile changes.

## Define the required capability first

Record:

- exact capability and lifecycle semantics;
- owner crate and public boundary;
- platforms and target configurations;
- safety policy, including required `unsafe_code` severity and permitted boundary shape;
- sync/async, allocation, trait-object, global-handler, thread, and shutdown constraints;
- dependency-source policy and forbidden alternative authorities;
- whether a first-party implementation is the selected fallback.

Do not select a crate merely because it removes a local compile error or exposes a convenient API.

## Build the candidate ledger

For every serious candidate, retain:

- current stable version and exact source, branch, tag, or revision;
- release recency, maintenance activity, successor or superseded status;
- license compatibility;
- Rust edition, stated MSRV, and toolchain policy;
- platform and target coverage;
- default and selected features;
- direct and transitive dependency footprint, including duplicate source/version consequences;
- unsafe implementation and lint policy, not merely safe public signatures;
- API, error, ownership, cancellation, and lifecycle fit;
- known advisories and the scope/date of the advisory check;
- acceptance, rejection, or unresolved reason.

Use local `~/strict-rs/*` checkouts first for strict-owned repositories. Use official manifests, source, releases, and advisories as primary external evidence. Do not rely on a wrapper's marketing summary for safety or lifecycle semantics.

Retain rejected candidates and reasons so compaction does not trigger the same research again. Refresh only facts likely to have drifted or when the required capability changes.

## Preserve the research boundary

- Do not add, remove, or change production dependencies, manifests, patches, or lockfiles during candidate review.
- A disposable POC requires explicit authorization, remains outside product checkouts, and proves only the tested property.
- A resolved POC graph is evidence, not production source authority.
- Read access to a neighboring strict checkout does not grant write, commit, push, or dependency-revision authority.
- Do not accept a broader or less safe crate merely to avoid a first-party implementation.

If no candidate satisfies the contract, present the first-party owner and irreducible platform boundary for review. Do not start that implementation unless authorized.

## Stop for selection

When the comparison is ready:

1. Reconcile the living goal with the full ledger, selected requirements, and remaining work.
2. Mark the goal blocked.
3. Present the candidate comparison and recommendation without modifying production authority.
4. Wait for explicit user review and selection.

After approval, hand the exact selected provenance and migration contract to `$upgrade-strict-dependencies`. Do not reopen rejected candidates unless new evidence contradicts the ledger.
