# Entry-path-matrix variant

## Concrete intent

Persist a reusable audit derived from the current `$auto-skill-creator` failure, where `Do not use for user-selected manual skill work` was incorrectly allowed to negate a direct manual invocation of the automatic skill itself.

## Approach

Enumerate conversational, harness, implicit, lifecycle, and handoff entry paths separately, then distinguish activation, evidence availability, and effect authority for each.

## Preserved nuance

The word `manual` is insufficient because manual ordinary work and manual invocation of an automatic skill have opposite routing outcomes. A bundle can be useful evidence without being an activation prerequisite, and explicit invocation does not expand external-effect authority.

## Relationships and uncertainty

This candidate overlaps system `$skill-creator`, `$auto-skill-enhancer`, `$auto-skill-creator`, and always-loaded trigger routing. Review should determine whether a standalone audit is more reliably reachable than distributing entry-path tests among those owners.

## Review questions

- Should the matrix also cover named plugin skills and connector-triggered skills?
- Is direct invocation truly unconditional when a skill package is present but deliberately disabled by harness policy?
