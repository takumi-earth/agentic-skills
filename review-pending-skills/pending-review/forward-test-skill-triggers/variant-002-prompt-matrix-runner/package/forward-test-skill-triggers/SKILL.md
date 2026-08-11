---
name: forward-test-skill-triggers
description: "Generate context-isolated skill-evaluation packets and validate externally collected result ledgers. Use when a changed skill needs repeatable explicit, implicit, nearest-negative, mixed-owner, and unauthorized-effect test cases. The bundled runner creates inert packets only; it does not launch agents or grant delegation authority."
---

# Forward-Test Skill Triggers

Generate repeatable evaluation inputs without embedding the expected answer.

## Define the matrix

Create a JSON specification containing the skill package locator and cases with stable IDs, prompt text, raw artifact locators, evaluation kind, and allowed effects. Keep expected activation and verdicts in a separate evaluator-only section so worker packets cannot reveal them.

Read [the result-ledger contract](references/result-ledger.md), then run:

```bash
python3 scripts/build_prompt_matrix.py build <matrix.json> <packet-directory>
```

The command writes one inert packet per case plus a manifest. It never starts an agent.

## Collect and validate externally

After separately authorized fresh agents run the packets, record their outputs in a JSON result ledger and validate it with:

```bash
python3 scripts/build_prompt_matrix.py validate <matrix.json> <results.json>
```

Require one result for every case, stable case identities, explicit context-isolation metadata, separate activation and execution verdicts, and no undeclared effects. A structurally valid ledger is not proof that the judgments are correct; inspect raw outputs and evaluator rationale.

## Prevent contamination

Do not put expected answers, diagnoses, desired fixes, or pass/fail labels in worker-visible packets. Reject results that inherited the source conversation, read evaluator-only fields, or discovered artifacts from a previous case.
