# No-op reporting-vocabulary variant

## Concrete intent

Make `guarded no-op` understandable at first use by spelling out the matched guard, already-satisfied desired state, and zero-write result.

## Approach

Standardize a concise human reporting template and contrast a successful no-op with blocked, skipped, failed, written, and later-verified outcomes.

## Preserved nuance

A no-op can be a successful application outcome without being a write. It does not imply broader build or repository verification.

## Relationships and uncertainty

This overlaps `$filesystem-git-observability` and `$design-command-observability`. Review should decide whether vocabulary alone warrants a skill or belongs in those existing owners.

## Review questions

- Should the phrase `guarded no-op` be retained at all, or replaced by plain language everywhere?
- Which target and condition fields are mandatory in a concise user-facing report?
