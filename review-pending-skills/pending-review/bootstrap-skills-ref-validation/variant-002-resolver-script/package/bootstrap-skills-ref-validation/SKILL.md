---
name: bootstrap-skills-ref-validation
description: "Inspect `skills-ref` validator availability and repository-pinned source provenance without installing anything. Use when the `skills-ref` CLI, `skills_ref` import, shorthand source path, package metadata, or helper executable state is unclear. The resolver emits typed discovery states and an inert install plan only."
---

# Bootstrap Skills-Ref Validation

Resolve the validator state without changing it.

## Run the bounded resolver

Read [the resolution states](references/resolution-states.md), then provide the canonical repository root and its declared pinned source path:

```bash
python3 scripts/resolve_skills_ref.py --repo <repo> --source <repo-relative-source>
```

The resolver reports CLI discovery, module importability and origin, source existence, project metadata, version agreement, dependency declarations, relevant helper modes, and an inert editable-install command. It does not search outside the provided repository and does not execute the plan.

## Interpret typed states

Treat `missing`, `present`, `mismatched-provenance`, `invalid-source`, and `unknown` as distinct states. A discovered CLI does not prove the module imports from the pinned source. A valid source tree does not authorize installation. A non-executable `.py` helper should be invoked through Python when its contract declares Python.

Pass `--json` for machine-readable output. Preserve expanded filesystem paths only internally; normalize home paths before persisting or presenting resolver output.
