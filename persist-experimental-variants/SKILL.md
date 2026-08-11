---
name: persist-experimental-variants
description: "Persist every materially different script, prompt, configuration, or design experiment as an immutable variant with its concrete intent and predecessor relationships. Use during scratchpad iteration when repeatedly editing one artifact would erase useful approaches, when recurrence is not yet knowable, or when later review may converge several variants. Do not use for pending skill-candidate evolution owned by `$review-pending-skills` or as a replacement for repository history."
---

# Persist Experimental Variants

Treat exploratory files as a design notebook. Copy, edit, and document variants so later review can reconstruct what each approach attempted without relying on Git history or one repeatedly overwritten scratch file.

## Preserve before generalizing

- Do not require recurrence before persistence. The first occurrence is the only opportunity to preserve the first approach accurately.
- Do not require use-case-agnostic architecture. Keep repository-specific paths, formats, assumptions, and concrete constraints when they define why the experiment exists.
- Do not collapse speculative variants into one preferred design. Separate files make comparison, sleep-on-it review, and later convergence possible.
- Do not delete an earlier approach merely because a later one works better. Record successor and convergence relationships explicitly.

## Create an immutable script variant

For a single script file, use the packaged helper:

```bash
python3 scripts/create_script_variant.py \
  --source ~/scratch/experiment.py \
  --notebook-id sqlite-query-approaches \
  --variant-id variant-001-first-approach \
  --intent "Test the direct SQLite query before introducing an adapter"
```

The helper resolves the canonical Agentic Skills repository and defaults the notebook to `.scratchpad/persist-experimental-variants/<notebook-id>/`. Add `--predecessor <variant-id>` when the approach evolves another variant. Every predecessor must be unique, exist in that notebook, contain valid identity-matching metadata, and retain payload bytes matching its recorded digest; self-predecessors are forbidden.

The helper refuses symlink sources and existing variant identifiers, uses an exclusive claim so concurrent creators cannot replace one another or a pre-existing empty target, copies exact source bytes beneath `artifact/<source-name>`, and records the payload-relative path and SHA-256 digest in `variant.json`. This keeps sources named `intent.md` or `variant.json` separate from notebook metadata. It never edits a prior variant.

Use `--notebook-root <path> --external-deliverable` instead of `--notebook-id` only when the user explicitly selected that external directory as a task deliverable. The flag is an authority assertion, not a convenience override. Without it, external destinations fail closed. Diagnostic fixtures and workflow bookkeeping still belong beneath the canonical repository scratchpad.

On success, stdout remains one human-readable path and renders destinations beneath the user home as `~/...`; `~` expands only internally for filesystem I/O. Expected validation and filesystem failures emit `VARIANT_ERROR[<stable-code>]: ...` and exit with status `3` rather than a traceback.

For multi-file or non-script experiments, preserve the same design manually or add a sibling helper variant rather than silently broadening this single-file script.

## Document useful intent

Record:

- the concrete question or failure being explored;
- the approach and important assumptions;
- what differs from predecessors and neighboring variants;
- observed results without retroactively rewriting the original intent;
- unresolved questions and possible convergence inputs.

Do not include private hidden reasoning. Preserve reviewable design rationale, evidence, and decisions that another session needs to understand the artifact.

## Converge by creating another variant

When several approaches contribute to a final design, create a convergence variant and list all predecessors. Explain what it adopts and rejects. Keep the source variants intact until the user explicitly authorizes removal.

Run `python3 scripts/test_create_script_variant.py` after changing the helper.
