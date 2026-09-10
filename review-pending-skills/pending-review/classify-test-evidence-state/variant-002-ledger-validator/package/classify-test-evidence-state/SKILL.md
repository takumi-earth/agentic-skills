---
name: classify-test-evidence-state
description: "Validate JSON test-evidence ledgers that claim behavioral closure. Use when a plan, parity audit, goal, or worker report must distinguish written, compiled, executed, assertion, process, focused, and canonical states and link each claim to an exact command and scope. The validator checks ledger consistency, not test adequacy."
---

# Classify Test Evidence State

Make unsupported evidence-state transitions fail structurally.

## Inspect the supplied ledger

Read [the ledger schema](references/ledger-schema.md) and validate an existing supplied record. Classification does not authorize execution or persistence, including creation of another ledger. Each row identifies its owner, claimed contract, evidence state, scope, exact command when observed, assertions, process exit, and evidence locator. Gate acceptance additionally names the actual criteria and their observed result.

Use `unexecuted` when tests exist but no command ran. A `compiled` row observes a successful build command and establishes no test-body execution or assertions. Do not invent command metadata or call unexecuted rows failures.

## Validate

```bash
python3 scripts/validate_evidence_ledger.py <ledger.json>
```

The validator rejects impossible or unsupported combinations, including `process-passed` with nonzero exit, `assertions-passed` without execution, `canonical-gate-passed` without a canonical scope, and behavioral closure from `written` alone.

## Interpret narrowly

Exit `0` proves schema and transition consistency only. It does not authenticate observations or prove test adequacy, parity, or canonical acceptance. Attribute evidence to its source, configuration, and command inputs; changes can invalidate a current claim without deleting its historical result. A later verification ban does not erase previously obtained, still-applicable evidence. Run gates only under the existing task authority and report results separately.
