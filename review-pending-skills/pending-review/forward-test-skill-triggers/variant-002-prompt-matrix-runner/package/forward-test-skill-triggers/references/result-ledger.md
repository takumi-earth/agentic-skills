# Prompt matrix and result ledger

## Matrix input

```json
{
  "schema_version": 1,
  "skill": {"name": "example-skill", "package": "path/to/package", "sha256": "..."},
  "cases": [
    {
      "id": "implicit-positive",
      "kind": "implicit-positive",
      "prompt": "Natural user prompt",
      "artifacts": ["fixtures/input.json"],
      "allowed_effects": ["read", "inline-analysis"],
      "expectation": {"activation": "triggered", "execution": "contract-satisfied"}
    }
  ]
}
```

Worker packets omit `expectation`. The manifest retains a hash of each packet and the matrix source.

## Result ledger

```json
{
  "schema_version": 1,
  "results": [
    {
      "case_id": "implicit-positive",
      "context_mode": "fresh",
      "activation": "triggered",
      "execution": "contract-satisfied",
      "effects": ["read", "inline-analysis"],
      "output_locator": "results/implicit-positive.json",
      "contamination": false,
      "evaluator_rationale": "..."
    }
  ]
}
```

Validation requires exactly one result per case, fresh context, declared effects only, valid verdict enums, and an output locator. The runner does not launch agents or evaluate semantic correctness.
