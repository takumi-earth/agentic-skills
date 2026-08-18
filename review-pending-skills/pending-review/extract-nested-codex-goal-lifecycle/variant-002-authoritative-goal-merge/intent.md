# Authoritative goal-merge variant

## Concrete intent

Combine transcript lifecycle observations with a read-only authoritative goal-status source while preserving disagreements instead of treating either source as complete by itself.

## Approach

Accept normalized nested-call events plus typed authoritative records, select current status only from the authoritative source, and emit transcript confirmations and disagreements with separate provenance.

## Preserved nuance

The transcript explains what the agent attempted and observed; the goal store owns current status. Missing authority is reported, never silently replaced by a transcript inference.

## Relationships and uncertainty

This differs materially from `variant-001-schema-aware-nested-parser` because it depends on a second authority source. Review should decide whether access to that store belongs in a harness adapter rather than a portable skill.

## Review questions

- Which goal-store schemas and read-only adapters should be supported?
- Should a confirmed transcript event be treated as a transition claim or only an observation?
