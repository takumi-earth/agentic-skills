# Converged skill validation

## Concrete intent

Give package and toolchain validation a distinct owner, `$validate-skill-packages`, separate from evaluating an agent's skill selection and decisions.

## Predecessors and adopted behavior

- Adopt discovery, installation authority, and provenance guidance from `bootstrap-skills-ref-validation/variant-001-instruction-bootstrap`.
- Adopt bounded CLI, module, pinned-source, and helper discovery from `bootstrap-skills-ref-validation/variant-002-resolver-script`.
- Adopt explicit interpreter handling and per-validator command outcomes from `bootstrap-skills-ref-validation/variant-003-validation-driver`.

## Changes and corrections

Normal validation runs directly once tooling is known. Conditional bootstrap guidance and its resolver load only for missing or uncertain tooling. The resolver compares installed distribution metadata with the pinned version and explicitly distinguishes finding a module from importing it. The command driver preserves process and assertion outcomes, fails required reported assertion failures, decodes arbitrary output safely, and keeps progress on stderr while stdout remains JSON.

## Authority and remaining evidence

The user agreed to this separate validation package and all recommended dispositions and corrections in the current review, then requested pruning of superseded variants. Predecessor paths identify designs retained in Git history. This convergence introduces no installation or dependency mutation. Promotion, synchronization, and other enablement remain separately authorized effects. Structural checks and script tests do not prove fresh-context skill behavior.
