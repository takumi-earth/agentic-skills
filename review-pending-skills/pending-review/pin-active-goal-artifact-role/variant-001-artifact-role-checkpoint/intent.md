# Artifact-role checkpoint variant

## Concrete intent

Prevent a plan-status or completion answer from silently switching from the harness-designated active goal to a historical goal, sibling attachment, or evidence artifact.

## Approach

Require a short, read-only role checkpoint before answering: record the exact active goal path, classify only paths explicitly referenced by that goal, read the active goal through EOF, and source every mutable status claim from it.

## Preserved nuance

Historical goals may explain provenance but cannot supply current pending work. An artifact role never grants read, edit, execution, or completion authority beyond the user's instruction.

## Relationships and uncertainty

This overlaps `$resume-strict-context`, `$maintain-living-goal`, and always-loaded strict guidance. Review should decide whether a separate trigger improves compliance at the status-answer boundary or fragments an already clear owner.

## Review questions

- Should this remain a standalone checkpoint or become a narrow section of `$resume-strict-context`?
- Which explicit harness field, if any, should be required as the active-path source?
