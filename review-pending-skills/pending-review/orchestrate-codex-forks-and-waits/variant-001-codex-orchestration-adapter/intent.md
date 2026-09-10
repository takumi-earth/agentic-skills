# Codex orchestration-adapter variant

## Concrete intent

Translate a delegation request written for another coding harness into current Codex collaboration controls while honoring explicit history-isolation and polling instructions.

## Approach

Use an instruction-only adapter: distinguish inert translation from execution, preserve semantic requirements, choose exact Codex context controls, and launch or wait only under existing delegation authority. Unsupported explicit constraints remain visible instead of being silently discarded.

## Preserved nuance

The default full-history rule yields to explicit history restrictions. No prior history means no inherited turns; a small positive count requires permission for limited history. Parent wait interruption does not stop a worker, and long waits grant no extra work.

## Relationships and uncertainty

This overlaps `$orchestrate-strict-work` and Codex collaboration-tool guidance. Review should decide whether the adapter belongs inside that strict owner or as a harness-neutral migration aid.

## Review questions

- Preserve the exact context request; do not replace zero history with a positive turn count.
- Which foreign-harness concepts should be translated and which should be rejected as unsupported?
