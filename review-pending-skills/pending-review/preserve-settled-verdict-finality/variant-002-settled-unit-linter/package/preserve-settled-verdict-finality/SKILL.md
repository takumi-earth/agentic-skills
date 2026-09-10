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

The script tracks unit headings such as `### U1` through their subsections and excludes explicit historical regions and fenced examples. It separates supported English prohibitions and checks of guards, hashes, inputs, source, configuration, or application readiness from requests to reassess the decision itself. It examines clauses separately, so a prohibition for one unit does not hide a reopening for another.

Findings are advisory: `decision-reopening` identifies explicit decision or countersignature wording; `needs-context` identifies an unqualified reassessment whose target remains uncertain. Exit `1` means review these signals, not that semantic reopening is proved; exit `0` means no signal in this bounded vocabulary, and malformed inputs exit `2`. Do not turn an unknown phrase or clean scan into a verdict.

## Preserve authority boundaries

Require real user provenance before placing a unit in a terminal state. A nonempty provenance or supersession string is a caller assertion that still needs attribution to actual user input; the linter cannot authenticate it. Changed application conditions can block effects without reopening the user's selection. Use existing task records; classification does not authorize creating a ledger. A clean lint does not prove the verdict, authorize application, or mark a goal complete.

Validate clean history, operative reopening, explicit user supersession, malformed ledger, nested history markers, and a unit mentioned outside its own section.
