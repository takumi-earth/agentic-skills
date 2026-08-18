# Schema-aware nested-parser variant

## Concrete intent

Recover real Codex goal lifecycle calls nested inside `functions.exec` custom tool calls without matching quoted, commented, or self-referential text.

## Approach

Parse rollout JSONL by record type, scan only completed `exec` tool inputs with a small JavaScript lexical boundary, extract `tools.update_goal(...)` calls outside strings and comments, and correlate them with matching custom tool outputs.

## Preserved nuance

A call observation and a confirmed successful output are separate evidence states. Transcript evidence remains observational and does not supersede a typed harness goal store.

## Relationships and uncertainty

The likely resource owner is `$skill-researcher`; this pending standalone package preserves the alternative for review instead of editing that official skill automatically.

## Review questions

- Should the parser become a resource repair inside `$skill-researcher` rather than a promoted skill?
- Which future nested-call encodings should be supported without accepting arbitrary JavaScript?
