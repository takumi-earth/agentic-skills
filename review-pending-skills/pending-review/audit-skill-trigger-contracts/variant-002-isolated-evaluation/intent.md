# Isolated-evaluation convergence

## Concrete intent

Keep skill entry-path auditing and isolated behavioral evaluation under `$audit-skill-trigger-contracts`, with evaluation mechanics loaded only when needed.

## Predecessors and adopted behavior

- Adopt the six independent routing verdicts and explicit-invocation protections from `audit-skill-trigger-contracts/variant-001-entry-path-matrix`.
- Adopt fresh-context evaluation, separate activation and execution judgments, and contamination review from `forward-test-skill-triggers/variant-001-isolated-evaluation-protocol`.
- Adopt inert packet generation and external result-ledger validation from `forward-test-skill-triggers/variant-002-prompt-matrix-runner`.
- Preserve the effect classifications folded into the existing audit owner from `separate-review-evidence-effects/variant-001-effect-classification-template`.

## Changes and corrections

The convergence gives the existing audit owner an optional evaluation mode. Worker packet identifiers are opaque, evaluation categories remain evaluator-only, packet files cannot collide with the manifest, and malformed matrices stop before field access. Result-ledger validity remains separate from whether observed behavior matches expectations. A matrix digest ties collected results to the evaluated inputs.

## Authority and remaining evidence

The user agreed to this ownership structure and all recommended dispositions and corrections in the current review, then requested pruning of superseded variants. Predecessor paths identify designs retained in Git history. This draft does not edit the official package, launch evaluators, change invocation policy in an installation, or authorize promotion or enablement. Direct script tests and local scenarios do not establish independent fresh-context trigger performance.
