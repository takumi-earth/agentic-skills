# Typed role-report variant

## Concrete intent

Make active-versus-historical goal attribution inspectable without scanning sibling attachments or changing any goal.

## Approach

Generate a deterministic JSON report from one exact active path plus caller-supplied historical or evidence references. Require each secondary path to appear literally in the active goal and reject conflicting roles.

## Preserved nuance

The report proves only path attribution. It does not decide status, authorize additional reads, or establish permission to edit or complete a goal.

## Relationships and uncertainty

This is a mechanical alternative to `variant-001-artifact-role-checkpoint` and overlaps `$resume-strict-context`. Review should decide whether literal reference proof is useful enough to justify a bundled script.

## Review questions

- Should reference matching recognize Markdown link normalization beyond literal path text?
- Should the script remain report-only even if promoted into a goal-maintenance workflow?
