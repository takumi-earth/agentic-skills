---
name: link-agentic-skills
description: Set up, preview, sync, route, and prune relative, per-skill symlinks from a canonical Agent Skills repository into local user-level agent harness skill directories. Use when the user asks to manage repository-owned skill links across one or more local harnesses. Do not use for root-level repository links, copying packages, plugin or marketplace installation, explaining generic skill discovery, or replacing unrelated destination entries.
---

# Link Agentic Skills

Use the bundled Python CLI to make one canonical skill repository available to multiple local harnesses without merging their roots or copying package contents.

## Establish the boundary

1. Resolve the bundled script relative to the activated skill directory, then resolve the canonical source repository. The CLI defaults to the repository containing this package after resolving package symlinks. Pass `--skills-root` whenever the user names another checkout, a plugin repository's flat `skills/` directory, or an ambiguous default.
2. Select only immediate, visible child directories containing a root `SKILL.md`. Preserve each complete package through a directory symlink.
3. Never link the repository root, recursively discover nested skills, copy packages, create junctions, or substitute absolute links.
4. Treat installed harness directories as deployment targets. Do not edit a linked package there; edit its canonical repository source.

## Choose default or configured routing

Without a config, route every discovered source skill to `~/.agents/skills` and every detected built-in harness. A built-in harness is detected when its skill directory or harness configuration root exists. A missing skill-directory child is created under an existing harness root. Missing harnesses are normal skips.

When a config exists, or when the user requests custom harnesses, allowlists, exclusions, or future-skill policy, read [configuration.md](references/configuration.md) before proceeding. Config presence is authoritative: only its named harness sections participate.

Use `init-config` only when persistent routing policy is wanted. It seeds `agents` plus currently detected built-ins, refuses to overwrite an existing config, and does not create harness links.

## Preview before changing links

For a review, explanation, or preflight request, run only a dry run. Require Python `3.11+`, resolve the script path from this skill package, then run:

```text
python3 "<skill-package>/scripts/link_agentic_skills.py" sync --dry-run
```

Add `--skills-root "<canonical-repository>"` when the source is not the default. Add `--config "<config-path>"` when the user selected a nonstandard config path.

Inspect the JSON report for the exact `source_root`, discovered `source_skills`, config changes, harness destinations, relative targets, removals, conflicts, and errors. A dry run must not write config, create directories, or change links.

If the request authorizes mutation and the preview matches the requested scope, rerun the same command without `--dry-run`:

```text
python3 "<skill-package>/scripts/link_agentic_skills.py" sync
```

Do not infer authorization to initialize config, edit routing policy, or reconcile additional source repositories merely from authorization to sync the current one.

## Preserve link ownership

- Leave a correct repository-owned relative link unchanged, including an equivalent relative spelling.
- Remove a deselected or stale link only when it is a relative link that lexically targets this repository's same-named package.
- Preserve files, directories, absolute symlinks, and links to other repositories as conflicts. Continue reconciling independent entries and return partial-failure status.
- If relative links cannot be created across filesystems or the platform denies symlink creation, report the error. Do not fall back to copies, junctions, or absolute symlinks.
- After any conflict or error, stop the workflow and report the structured result. Never improvise an overwrite, deletion, compatibility fallback, or additional mutation.

## Interpret and report outcomes

- Exit `0` means every active destination converged; missing detected harnesses may have been skipped.
- Exit `1` means an operational error or preserved conflict caused partial convergence. Successful independent actions remain valid.
- Exit `2` means the source, command line, or configuration was invalid and no harness reconciliation began.

Treat JSON on stdout as the complete machine-readable result and stderr as human-readable diagnostics. Report exact source and destination paths, whether config changed, created/unchanged/removed links, skipped harnesses, preserved conflicts, and process exit status. Do not claim a full sync when the command returned `1` or `2`.

For an initialized policy, preview first:

```text
python3 "<skill-package>/scripts/link_agentic_skills.py" init-config --dry-run
```

Create it only with authorization by removing `--dry-run`.
