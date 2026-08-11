---
name: challenge-legacy-precedent
description: "Review whether a helper API makes a prohibited implementation or test shortcut the easiest path. Use when APIs return rendered strings, accept fixed paths or complete bodies, expose global occurrence counts, collapse outcomes to booleans, mutate the first match, or hide textual fallback behind semantic names."
---

# Challenge Legacy Precedent

Inspect the stable helper boundary before copying its call pattern.

## Trace the incentive

Read [the API incentive checklist](references/api-incentive-checklist.md). Map each input, output, default, fallback, and error state to the behavior it encourages.

Flag APIs that:

- return raw rendered source from structural operations;
- take an authoritative file path instead of a complete scope;
- accept a complete upstream body, fingerprint, marker, or hash as identity;
- return `bool`, `None`, or unchanged source for absence, ambiguity, drift, and post-state;
- mutate while discovery is incomplete or stop at the first match;
- make global string counts easier than owner-scoped typed queries;
- silently invoke Git or textual fallback after structural discovery fails.

## Demand the counter-API

Prefer typed owners, semantic queries, candidate sets, explicit state variants, planned edit sets, opaque structural results, and separate diagnostic rendering. Require an explicit exact-output layer for legitimate text contracts.

Do not classify every string, path, boolean, or first-match operation as wrong. The defect exists when the representation carries load-bearing semantic, causal, or evidence authority that the protected contract does not permit.
