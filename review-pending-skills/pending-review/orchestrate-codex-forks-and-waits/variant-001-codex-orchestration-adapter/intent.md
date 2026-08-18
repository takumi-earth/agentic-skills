# Codex orchestration-adapter variant

## Concrete intent

Translate a delegation request written for another coding harness into current Codex collaboration controls while honoring explicit history-isolation and polling instructions.

## Approach

Use an instruction-only adapter: confirm explicit delegation authority, extract semantic requirements rather than foreign commands, choose Codex fork context, send a self-contained assignment, and wait through the native mailbox mechanism.

## Preserved nuance

The default full-history rule yields to the user's explicit no-full-history instruction for the named workflow. Long waits do not authorize extra work or repeated progress polls.

## Relationships and uncertainty

This overlaps `$orchestrate-strict-work` and Codex collaboration-tool guidance. Review should decide whether the adapter belongs inside that strict owner or as a harness-neutral migration aid.

## Review questions

- How much recent context is the minimum safe fork when the user rejects full history?
- Which foreign-harness concepts should be translated and which should be rejected as unsupported?
