---
name: persist-experimental-variants
description: "Persist every materially different script, prompt, configuration, or design experiment as an immutable variant with its concrete intent and predecessor relationships. Use during scratchpad iteration when repeatedly editing one artifact would erase useful approaches, when recurrence is not yet knowable, or when later review may converge several variants."
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
  --notebook-root ~/scratch/variant-notebook \
  --variant-id variant-001-first-approach \
  --intent "Test the direct SQLite query before introducing an adapter"
```

Add `--predecessor <variant-id>` when the approach evolves another variant. The helper refuses symlink sources and existing variant identifiers, copies the source bytes, records a SHA-256 digest, and writes `intent.md` plus `variant.json` atomically inside a new directory. It never edits a prior variant. It renders output beneath the user home as `~/...`; it expands `~` only internally for filesystem I/O.

For multi-file or non-script experiments, preserve the same structure manually or add a new helper variant rather than silently broadening this file-oriented script.

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
