# Artifact-lifecycle variant

## Concrete intent

Preserve the distinction that corrected the active task: implementing a complete hook or skill artifact is useful and authorized independently of registering, synchronizing, or otherwise enabling it.

## Approach

Model the lifecycle as four observable artifact states—created, adopted, registered or distributed, and active—then choose the least-active correct output location and validate there.

## Preserved nuance

This variant explicitly handles canonical files that are already symlinked or dynamically loaded, where an apparently ordinary source edit can itself be activation. It also prevents lack of enablement authority from being used as an excuse to omit an inert deliverable.

## Relationships and uncertainty

The behavior overlaps always-loaded artifact-boundary guidance and `$auto-skill-creator`, but a dedicated reusable workflow may still be easier to trigger for hooks, configuration examples, templates, and integrations. Review should decide whether that trigger is useful or whether the global kernel plus another owner is sufficient.

## Review questions

- Should adoption and registration remain separate states for every artifact type?
- Should this remain a standalone skill or become a shared reference used by artifact-specific skills?
