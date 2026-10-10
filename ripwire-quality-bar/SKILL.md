---
name: ripwire-quality-bar
description: >
  Code QUALITY of what YOU just wrote: --quality-delta gates major preexisting regressions; review
  all debt. A measured shape (humps/deep, a tangle) selects the refactor. Merge safety → change-check.
  Even a single-line leaf fix runs the one-shot delta.
allowed-tools: Bash, Read
---

> Modified canonical port: compact instructions and conditional references are maintained in `~/agentic-skills`; upstream skill-definition enhancements use `$manage-ripwire-skills`.
# Check the change once, then disclose the needed mode

Use only within the current code-change and verification authority. A verification ban excludes this check and substitute source audits. Another symbol or retained-context continuation does not require rereading the skill.

For an authorized code change, run `ripwire <dir> --quality-delta`. In a Git repository it compares the working tree with `HEAD` by default; no baseline ritual is required. The delta covers **10 kinds**. In a shared tree, use explicit owned paths with `--scope=GLOB`; `--scope=diff` also includes sibling changes.

Read the result before declaring quality:

- `gating=` counts major unacknowledged regressions of preexisting symbols; those make exit `2`.
- Minor and `origin="new-symbol"` rows are printed but do not gate. Exit `0` does not prove no added debt.
- Renamed/moved symbols can appear new. Inspect their rows rather than treating a green exit as preserved quality.
- Out-of-scope rows remain visible and cannot be acknowledged as this task's work.

For a **single-line leaf fix** with a clean delta and no unresolved material row, stop. Do not add `--quality-panel`, DMM, acknowledgements, repeated checks, or the convergence playbook merely because the skill activated.

For findings, a measured shape, shared-tree acknowledgements, baselines, `ev=`/nesting profiles, or CI integration, load [convergence.md](convergence.md). It owns the scope-safe acknowledgement rules, shape-to-refactor preconditions, and complete fix loop: `--quality-delta` → `--edit-check=SYM` → `--affected` and the authorized tests. Use the repository's accepted gate surface; a suggested test list cannot replace it.

Structural metrics describe a candidate problem; they do not prescribe a computed fix or establish runtime heat. Never split code, delete a clone, weaken a test, or widen scope merely to improve a number. Stop blind refinement after the bounded rounds in the reference.

Baseline, acknowledgement, note, and hook writes need task authority. Do not accept another session's debt, install CI, or change thresholds because this skill was invoked. Full metric definitions and evidence are in [quality-metrics.md](quality-metrics.md), loaded only when interpreting a named metric requires them.
