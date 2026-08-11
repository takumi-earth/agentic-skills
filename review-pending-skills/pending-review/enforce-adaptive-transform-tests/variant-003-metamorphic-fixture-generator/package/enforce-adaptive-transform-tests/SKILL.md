---
name: enforce-adaptive-transform-tests
description: "Generate metamorphic fixture cases for adaptive parsed-source transformations from one minimal typed JSON model. Use when tests must cover formatting, reordering, file movement, unrelated extension, decoys, ambiguity, drift, recognized post-state, replay, and irrelevant dependency-version changes without copying full expected source snapshots."
---

# Enforce Adaptive Transform Tests

Derive controlled variations from one small semantic model; keep the oracle typed and owner-aware.

## Define the fixture model

Read [the fixture model](references/fixture-model.md). Declare semantic owner, target operation, original path, permitted moved path, unrelated owner, candidate polarity, and relevant source fragments. Keep fragments minimal and version-neutral.

## Generate cases

```bash
python3 scripts/generate_metamorphic_cases.py <model.json> --output <cases.json>
```

The generator emits named variation instructions and expected typed outcomes. It does not emit full expected transformed source and does not execute the transformation.

## Use one oracle

Apply the same transformation declaration and typed assertions to every case. Prove the discovered path follows movement, unrelated owners are unchanged, ambiguity and drift produce zero edits, post-state is recognized, and replay has an empty delta. Change the model only when the semantic contract changes, not for formatter or upstream trivia variation.

Keep product behavior at its real owner and exact text contracts in a separate layer. Generated case volume is not coverage unless the authorized tests execute and assert the intended relationships.
