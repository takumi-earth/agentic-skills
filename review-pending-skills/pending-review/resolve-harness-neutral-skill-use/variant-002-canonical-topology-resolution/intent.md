# Canonical topology-resolution variant

## Concrete intent

Resolve copied, symlinked, and canonical skill projections into explicit topology facts before correlating them with transcript evidence.

## Approach

Inspect only caller-supplied package or `SKILL.md` paths, resolve each lexical projection to its canonical target, hash the body, and group identical content without asserting that copied paths share one mutable identity.

## Preserved nuance

Canonical target identity, byte equality, and harness availability are separate facts. The script is read-only and does not link or synchronize anything.

## Relationships and uncertainty

This differs from `variant-001-harness-catalog-resolution` by making deployment topology primary. It overlaps `$link-agentic-skills` and `$validate-symlinked-skill-runtime` but performs no deployment effect.

## Review questions

- Should canonical identity use filesystem target, package metadata, or repository-relative origin?
- How should copied packages with identical bytes but independent evolution be displayed?
