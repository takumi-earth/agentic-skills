---
name: validate-skill-packages
description: "Validate skill packages with declared canonical and harness validators, and resolve missing or uncertain validator tooling when needed. Use for package validation, pinned skills-ref provenance, or Python helper invocation problems. Do not use to judge agent trigger performance or as authority to install tools, substitute gates, or enable a skill."
---

# Validate Skill Packages

Run the requested package checks and report what each gate actually established. Keep toolchain validation separate from behavioral evaluation owned by `$audit-skill-trigger-contracts`.

## Use known validators directly

Read repository validation guidance and identify the exact packages and required canonical, harness, and supplemental gates. Use existing package test entry points for added or changed scripts. A required canonical gate remains required even when a harness check passes.

Run the established commands directly for a simple check. When a declared multi-validator plan or separate process/assertion accounting is useful, read [the validator plan contract](references/validator-plan.md) and use `scripts/run_skill_validators.py`. Do not create a durable plan or report merely for routine validation; use transient inputs under the resolved canonical repository's `.scratchpad/` when a plan is needed.

## Resolve tooling only when uncertain

Read [the bootstrap procedure](references/bootstrap.md) when the CLI, module discovery, pinned-source provenance, installed version, or helper interpreter is missing or unclear. Its read-only resolver reports discovery and version comparison without installing tools or importing the target module.

Do not infer installation authority from source presence or a missing validator. Present a concrete install plan when installation is required, then act only within explicit environment-mutation authority. Do not substitute another validator or change caches and temporary directories to work around a failed intended command.

## Interpret outcomes

- Separate process start, exit code, explicit assertion outcome, timeout, and each required or optional gate.
- An explicit required assertion failure or a nonzero required process exit fails the aggregate gate. Unreported assertions stay `not-reported`; do not invent a pass.
- A non-executable Python helper is invoked with its declared interpreter. A permission or sandbox failure in the intended command requires escalation rather than a changed command or cache location.
- Report the packages and commands actually checked. Successful structural validation and direct script tests do not establish correct agent activation, workflow behavior, promotion readiness, or enablement authority.

If isolated behavioral evaluation is required, route that question to `$audit-skill-trigger-contracts` and preserve delegation and context-isolation authority separately.
