---
name: render-hook-decision-failures
description: "Render typed hook policy or resolution results with the exact checked condition, expected value, received value, stage, and stable code. Use when a Codex PostToolUse boundary must convert a validated success-or-failure result into safe user-visible context; do not use custom top-level hook fields or stderr diagnostics."
---

# Render Hook Decision Failures

Apply the `variant-001-typed-resolution-result` design without silently merging it with sibling approaches.

## Preserve authority

- Treat this nested package as pending review until the user separately authorizes promotion and enablement.
- Preserve run-specific evidence in the canonical repository scratchpad and keep reusable product resources in this package.
- Do not register hooks, edit Codex source, change configuration, synchronize installations, stage unrelated work, or publish as an implied consequence of using this skill.
- Render paths beneath the user home as `~/...` and invoke environment-selected tools instead of hard-coded interpreter paths.

## Apply this design

Model success and failure with explicit `status`, `stage`, `code`, `condition`, `expected`, `received`, `candidate_count`, and optional `artifact` fields. Require nonempty `stage`, `code`, and `condition`; accept only bounded domain-selected diagnostic values; normalize paths beneath the home directory.

Render only this Codex envelope:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "..."
  }
}
```

Do not emit custom top-level `decision`, `mode`, or diagnostic objects. Keep stderr empty and return process status `0` for both a typed decision failure and a safe invalid-input diagnostic.

Use this sequence:

1. Identify the authority source and exact input facts before making a policy decision.
2. Apply only the contract documented in `references/approach.md` and its directly named resources.
3. Emit the checked condition, expected value, received value, and stable outcome whenever the design can fail.
4. Keep machine-readable output valid and separate from explanatory prose when a harness schema controls stdout.
5. Stop before any activation, synchronization, external mutation, or scope expansion not explicitly authorized by the user.

## Validate proportionately

- Prove one exact fixture for every failure code.
- Prove success path contains no failure language.
- Prove stdout remains one valid `PostToolUse` JSON object and stderr remains empty.
- Prove condition, expected, received, stage, and code are never omitted or empty.
- Prove malformed or unsafe values render a safe envelope without exposing the rejected input.

Report assertions and process exit status separately. A nonzero command is diagnostic evidence, not a passing gate.

## Guard known risks

- Guard against Exposing sensitive received values without redaction.
- Guard against Making human messages too verbose for hook context.
- Guard against Allowing unstable exception strings to become machine codes.
- Guard against Emitting custom top-level fields that Codex ignores.

## Load resources

- Read `references/approach.md` before applying this variant's design.
- Read `references/decision-result-schema.json` before accepting a typed result from another owner.
- Run `scripts/render_hook_decision.py` for the deterministic operation it owns; use its `--self-test` before relying on it.
