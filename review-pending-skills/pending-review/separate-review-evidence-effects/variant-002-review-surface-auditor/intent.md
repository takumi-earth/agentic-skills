# Review-surface-auditor variant

## Concrete intent

Emit line-located advisory findings when a review-oriented skill implicitly couples analysis to additional effects.

## Approach

Scan `SKILL.md` and direct Markdown references for phrases linking review triggers to artifact creation, collectors, probes, validation, mutation, Git, activation, or publication without an explicit authority boundary.

## Preserved nuance

Static findings are not authority judgments. Explicit deliverables and narrowly declared automatic pipelines may be legitimate and require contextual adjudication.

## Relationships and uncertainty

This executable alternative complements the effect template and overlaps `$audit-skill-trigger-contracts`. Review should tune false-positive rules from real packages before adoption.
