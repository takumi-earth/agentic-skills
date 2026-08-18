---
name: preserve-settled-verdict-finality
description: "Lint a plan or recovery document for operative reassessment language that reopens user-settled or applied decision units. Use when maintaining a long-lived verdict ledger and a deterministic text safeguard is warranted before presenting or applying a revised plan."
---

# Preserve Settled Verdict Finality

Use the bundled linter as a review safeguard, never as the source of a verdict.

## Prepare explicit inputs

Provide a JSON ledger:

```json
{"units":[{"id":"U1","state":"settled","user_provenance":"user instruction","user_supersession":null}]}
```

The supported terminal states are `settled`, `applied`, and `superseded-gate`. A nonempty `user_supersession` permits reopened wording for that unit.

Mark retained historical prose only with these exact delimiters:

```markdown
<!-- settled-verdict-history:begin -->
...
<!-- settled-verdict-history:end -->
```

Run:

```bash
python3 scripts/lint_settled_units.py --ledger <ledger.json> --document <plan.md>
```

The script tracks Markdown headings such as `### U1`, detects high-signal reassessment and countersignature phrases outside historical regions, emits JSON findings, and exits nonzero when it finds an operative reopening.

## Preserve authority boundaries

Require real user provenance before placing a unit in a terminal state. Treat a clean lint as text consistency only; it does not prove the verdict, authorize application, or mark a goal complete.

Validate clean history, operative reopening, explicit user supersession, malformed ledger, nested history markers, and a unit mentioned outside its own section.
