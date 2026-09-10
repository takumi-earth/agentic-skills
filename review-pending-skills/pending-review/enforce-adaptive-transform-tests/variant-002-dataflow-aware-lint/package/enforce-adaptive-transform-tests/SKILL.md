---
name: enforce-adaptive-transform-tests
description: "Analyze selected Python files for text-oracle laundering in adaptive parsed-source tests by following values derived from source parsing, syntax text, transformation output, or rendered workspaces into substring, regex, equality, snapshot, and wrapper assertions. Use for focused review or CI design; do not ban ordinary string tests globally."
---

# Enforce Adaptive Transform Tests

Classify assertions by value provenance and purpose instead of searching for one method name.

## Define sources and sinks

Read [the flow model](references/flow-model.md). Mark parsed-source rendering, syntax-node text, transformation output, snapshots, and helper return values as taint sources. Mark substring, regex, prefix, suffix, raw equality, snapshot, and copied-body checks as structural-oracle sinks only when the value derives from those sources.

## Run the bounded scanner

```bash
python3 scripts/lint_oracle_flow.py <test-file.py> [<another-test.py>]
```

The scanner emits findings with file, line, sink, and reason, plus explicit unknown-flow diagnostics. Exit `0` means no finding within the supported model, `1` means findings, `2` means input errors, and `3` means unknown coverage without findings. It is intentionally conservative and must not be reported as a complete compiler-grade dataflow proof.

## Adjudicate findings

- Replace structural text sinks with typed owner/node/outcome/delta queries.
- Preserve exact string assertions when text or bytes are themselves the documented contract.
- Reject parse-then-text and wrapper laundering even when the final assertion helper has an innocuous name.
- Treat large copied fixtures as review signals, not applicability fingerprints.

Do not modify test source, install a lint, or add a CI gate without separate authority. Run product tests and metamorphic behavior separately; a clean scan is not behavioral proof.
