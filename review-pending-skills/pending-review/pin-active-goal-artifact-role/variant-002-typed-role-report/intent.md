# Typed role-report variant

## Concrete intent

Make active-versus-historical goal attribution inspectable without scanning sibling attachments or changing any goal.

## Approach

Generate a deterministic JSON report from one exact active path plus caller-supplied historical or evidence references. Require each secondary path to appear literally in the active goal and reject conflicting roles.

## Preserved nuance

The report distinguishes a caller-declared role from a verified complete path mention. It does not prove semantic role or authority, read secondary contents, decide status, authorize additional reads, or establish permission to edit or complete a goal.

## Relationships and uncertainty

This is a mechanical alternative to `variant-001-artifact-role-checkpoint` and overlaps `$resume-strict-context`. Review should decide whether literal reference proof is useful enough to justify a bundled script.

## Review questions

- Literal path matching now recognizes complete absolute, home-relative, and goal-directory-relative spellings with ordinary delimiters; encoded URLs and indirect links remain outside the declared interface.
- Should the script remain report-only even if promoted into a goal-maintenance workflow?
