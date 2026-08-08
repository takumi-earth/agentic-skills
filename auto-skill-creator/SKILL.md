---
name: auto-skill-creator
description: "Apply explicitly approved user-level skill proposals from the retained current conversation or full-history fork. Use after `$auto-skill-enhancer` or `$skill-researcher` produces concrete proposals and the user clearly authorizes specific proposals, or when the user explicitly invokes `$auto-skill-creator` with an approved proposal retained in the conversation. Reuse `$skill-creator`; do not infer approval, research new candidates, edit unapproved skills, or run merely because a goal or session completed."
---

# Auto Skill Creator

Treat the user's approval as a closed mutation ledger. Recover the exact approved proposal, apply only that proposal through `$skill-creator`, validate the affected packages, and report the resulting scope precisely.

## Resolve the approved proposal

Use the retained visible current-conversation or full-history-fork chronology first. Do not require a goal record, completion hook, transcript path, session ID, or terminal session state when the proposal and approval are present in that history.

Identify:

- the complete proposal version;
- the affected skill names and user-owned package paths;
- whether each package is new or existing;
- the exact approved prose, diff hunks, resources, scripts, and invocation changes;
- the user message that approves all or a named subset;
- any later revision, revocation, superseding proposal, or scope correction.

A full-history fork preserves an earlier proposal and approval; copied history is not a second approval. Apply chronology once and honor the newest controlling user instruction.

Do not treat any of these as approval by themselves:

- a bare `$auto-skill-creator` invocation;
- vague positive feedback such as “looks good” or “interesting”;
- approval of one proposal as approval of its siblings;
- an assistant summary, compaction summary, memory entry, or final answer without the underlying proposal;
- approval that predates a later proposal revision;
- goal or session completion.

If the exact proposal is no longer retained, ask the user to paste or identify it. Do not require a session ID as the only recovery path, search for the newest rollout heuristically, or infer the proposal from current files.

## Freeze the mutation ledger

Before editing, state a compact ledger containing:

- the proposal identifier or unambiguous title;
- the approving user message;
- each target skill and absolute user-owned package path;
- `create` or `update` for each package;
- exact allowlisted relative paths;
- approved semantic changes and required scripts;
- package and script validation;
- explicitly excluded proposals, files, and adjacent cleanup.

For partial approval, include only the approved subset. For multiple proposal versions, require approval that unambiguously selects the version to apply.

Stop before mutation when:

- approval is absent, ambiguous, contradictory, revoked, or stale;
- an approved hunk overlaps later unapproved source changes;
- the proposal reaches another skill, system package, plugin cache, repository, hook, configuration, memory, or external system that was not approved;
- the requested path escapes the user-owned skill root;
- implementation requires a new design decision rather than a mechanical realization of the approved design.

## Use the existing owners

Read `$skill-creator` completely before changing a package and follow its initialization, resource, metadata, validation, and forward-testing workflow.

Reuse the system creator resources:

- use `init_skill.py` for a new skill package;
- use `generate_openai_yaml.py` when invocation-facing metadata changes;
- use `quick_validate.py` for structural validation;
- test every added or changed executable script directly;
- use fresh task-relevant agents for proportionate forward tests when the approved skill is behaviorally complex.

Keep each forward-test agent on one semantic assignment. Use follow-ups only to continue or correct that same slice; use a fresh agent for an unrelated scenario or topic.

Do not reopen the approved design, add adjacent cleanup, create auxiliary documentation, alter unrelated skills, or reinterpret an approved enhancement as broader portfolio authority. Return to `$skill-researcher` only when the user separately requests new candidate research.

## Guard the approved scope

Before mutation, run `scripts/skill_change_guard.py snapshot` for only the affected skill packages. Record absent packages explicitly as new targets.

Immediately before live changes, run `scripts/skill_change_guard.py unchanged`. If an affected package drifted after the snapshot, stop and reconcile that drift instead of overwriting it.

After mutation and validation, run `scripts/skill_change_guard.py verify` with every approved relative path allowlisted. Treat any unapproved target-package change as a failure. Ignore unrelated dirty sibling skill packages; never clean, restore, stage, commit, or rewrite them.

The guard proves filesystem scope only. It does not decide whether approval exists, parse conversation meaning, apply patches, initialize packages, generate metadata, or replace `$skill-creator` validation.

## Validate before claiming completion

For every affected package:

1. Run tests for each added or changed script.
2. Regenerate `agents/openai.yaml` when the approved trigger or interface changed.
3. Run the canonical `$skill-creator` structural validator.
4. Forward-test complex trigger or execution behavior with fresh agents when safe and proportionate.
5. Run the approved-scope verification.

If an implementation defect causes validation failure, repair it only within the approved ledger and rerun the affected validation. If correction requires a new semantic decision or file, stop and request approval.

Do not claim validation when a validator could not run. Report dependency, permission, and tooling failures separately from package correctness.

## Report the exact result

Report:

- the proposal or approved subset applied;
- every created or changed skill package and path;
- every script and validation command run;
- assertion and process results;
- the scope-guard result;
- unapproved or stale state deliberately left untouched;
- any remaining validation or approval blocker.

Do not mutate repositories, transcripts, memory, hooks, configuration, commits, or external systems unless the user separately authorized those exact surfaces.
