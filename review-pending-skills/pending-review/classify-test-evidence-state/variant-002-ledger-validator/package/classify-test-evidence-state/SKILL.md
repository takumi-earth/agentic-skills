---
name: classify-test-evidence-state
description: "Validate JSON test-evidence ledgers that claim behavioral closure. Use when a plan, parity audit, goal, or worker report must distinguish written, compiled, executed, assertion, process, focused, and canonical states and link each claim to an exact command and scope. The validator checks ledger consistency, not test adequacy."
---

# Classify Test Evidence State

Make unsupported evidence-state transitions fail structurally.

## Write the ledger

Read [the ledger schema](references/ledger-schema.md). Give every row an ID, semantic owner, claimed contract, evidence state, scope, command identity when executed, assertion result, process exit status, and evidence locator.

Use `unexecuted` explicitly when tests exist but no command ran. Do not invent command metadata or call unexecuted rows failures.

## Validate

```bash
python3 scripts/validate_evidence_ledger.py <ledger.json>
```

The validator rejects impossible or unsupported combinations, including `process-passed` with nonzero exit, `assertions-passed` without execution, `canonical-gate-passed` without a canonical scope, and behavioral closure from `written` alone.

## Interpret narrowly

Exit `0` proves schema and transition consistency only. It does not prove the tests observe the right owner, provide parity, or satisfy the repository's canonical command. Run those gates only with separate authority and report their results independently.
