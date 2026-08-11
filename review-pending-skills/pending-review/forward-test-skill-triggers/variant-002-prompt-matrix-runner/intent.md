# Prompt-matrix-runner variant

## Concrete intent

Generate contamination-resistant evaluation packets and validate result-ledger completeness without launching agents.

## Approach

Separate worker-visible prompts and artifacts from evaluator-only expectations, emit stable case manifests, and validate externally gathered activation and execution results with isolation and effect metadata.

## Preserved nuance

Packet generation is inert. Delegation, agent launch, and any live effect require separate authority; valid ledger structure does not prove evaluator judgment.

## Relationships and uncertainty

This executable alternative overlaps `$audit-skill-trigger-contracts` and complements the protocol variant. Review should decide whether external harness adapters warrant separate variants.
