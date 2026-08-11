# Evidence-state-protocol variant

## Concrete intent

Prevent written test code, compilation, execution, assertion success, process success, focused gates, and canonical acceptance from collapsing into one `covered` label.

## Approach

Define a monotonic evidence lattice with precise allowed reporting language and explicit transitions. Preserve `written but unexecuted` as implementation when verification is forbidden.

## Preserved nuance

This protocol classifies evidence already obtained. It never authorizes running a command and does not assess whether a passing test observes the correct semantic owner.

## Relationships and uncertainty

This overlaps `$verify-test-parity`, `$maintain-living-goal`, and `$verify-strict-work`. Review should decide whether a general protocol is more useful than keeping the rule within phase-specific owners.
