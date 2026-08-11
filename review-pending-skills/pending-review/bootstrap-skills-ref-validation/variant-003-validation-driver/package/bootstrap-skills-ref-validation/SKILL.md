---
name: bootstrap-skills-ref-validation
description: "Run canonical and harness skill validators with explicit interpreter handling and separate command outcomes. Use when validating one or more skill packages after validator availability is already resolved, especially when bundled Python helpers are not executable. Do not install dependencies or replace a missing canonical gate."
---

# Bootstrap Skills-Ref Validation

Run declared validators without collapsing their results.

## Define validator commands

Read [the validator contract](references/validator-contract.md). Provide one JSON plan containing package paths and validator entries with stable IDs, command arguments, validator kind, and whether the command is required.

Invoke the driver:

```bash
python3 scripts/run_skill_validators.py <plan.json>
```

For Python files, declare `interpreter: python3`; the driver invokes the interpreter explicitly rather than requiring an executable bit. Declare CLI validators as argument arrays without a shell.

## Preserve outcomes

Record each command's start status, exit code, bounded standard output and error, package scope, and required/optional classification. Report inner assertions separately from the process result when the validator exposes both. Overall success requires every required command to exit `0` for every declared package.

The driver does not install missing tools, add fallbacks, redirect caches, or mutate packages. A missing canonical validator remains a typed unavailable result, even if a harness-specific validator succeeds.
