---
name: manage-ripwire-skills
description: "Use in addition to `$manage-ripwire-repo` only for Ripwire skill enhancements, changes, or review of proposed skill changes. Compare committed upstream definitions with archived bases and canonical customized ports, and reconcile authorized changes without losing local policy or reference splits. A general pull, build, compiler repair, or binary installation does not trigger this skill."
---

# Manage Canonical Ripwire Skills

`~/agentic-skills` owns the ported definitions. The tool checkout supplies upstream input; its installer and installed copies are not the skill source of truth. Preserve local permission boundaries, compact entrypoints, conditional references, and harness-neutral behavior.

Apply `$manage-ripwire-repo` for repository context and this skill as the additional owner of the requested skill work. When editing the canonical source, `$manage-agentic-skills-repo` owns that repository's Git workflow. Merely pulling, building, or installing Ripwire does not request a skill comparison or update.

## Choose the requested effect

- For a requested comparison of skill enhancements, check the committed revision, including the revision produced by an already-completed pull or installation. Do not run `git pull`, fetch, reset, install the binary, synchronize links, or register hooks merely because this skill activates.
- A compare-only request returns drift and review leads without source edits or baseline advancement.
- A request to update the ports authorizes compatible reconciliation of existing canonical definitions. New skill adoption, capability retirement, distribution, configuration, commits, and publication remain separate effects.

Run from this package with Python `3.11+`:

```bash
python3 scripts/manage_ripwire_skills.py check
```

Defaults are the user-selected `~/agentic-skills` and `~/github-forks/ripwire`; pass `--skills-root` or `--upstream-repo` for another explicit checkout. `--ref` selects a committed revision and defaults to `HEAD`. Working-tree edits are not treated as a new upstream release.

## Interpret the comparison

The helper reads the self-contained archive in `assets/upstream-baseline.json`; it does not need old Git objects to reconstruct accepted upstream bytes. Bases are per package, so deferred work does not erase already-reviewed progress.

Distinguish `upstream-current`, `review-required`, new/removed upstream packages, and missing canonical packages. File leads distinguish upstream-only drift, both sides changed, and an already-equal local result. Hashes and byte differences detect external file drift; they do not establish semantic equivalence or select a source transformation.

When a committed definition changed, read its complete affected contract and resources, the archived base, and our canonical owner. A moved paragraph may already live in a conditional reference. Do not replace an entire customized `SKILL.md`, restore upstream installer guidance, lose our OpenAI metadata or notices, or copy the full upstream repository into scratch.

No definition drift is a factual source comparison, not proof that every new runtime feature is documented. If the task also requires CLI compatibility, verify the relevant claimed flags against the matching binary or owning source within its authorized scope.

## Reconcile and checkpoint an authorized update

Load [update-workflow.md](references/update-workflow.md) only when source reconciliation or baseline advancement is authorized. It owns the review dispositions, validation barrier, and stale-input guards.

Preserve local designs while adopting real upstream corrections and capabilities. Validate every changed package with the canonical and harness validators and directly test changed scripts. Apply realistic positive and negative routing controls when a trigger changes; independent agents require explicit delegation authority.

The helper never writes canonical skill bodies. Its `acknowledge` command records reviewed upstream bases only after a fresh report and explicit per-package dispositions. Deferred units retain their old bases and remain pending. Upstream deletion does not delete our canonical capability; record that upstream fact separately from a user-authorized local retirement.

Initialization is a first-import effect, not an update shortcut. Never reinitialize the archive to hide unresolved drift or treat an agent-authored disposition as new user authority.

## Report the reached state

Report the upstream revision, changed packages, adopted versus preserved local behavior, deferred decisions, validator results, and whether a baseline changed. Separate source alignment, runtime acceptance, distribution, and user acceptance. Do not call pending or merely acknowledged units fully verified.

Direct tests: `python3 scripts/test_manage_ripwire_skills.py`. All generated reports and test fixtures belong under the explicit canonical repository's `.scratchpad/`. Package lookup does not establish repository authority, and copied or symlinked execution must use the same declared roots.
