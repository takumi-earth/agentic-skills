---
name: manage-ripwire-repo
description: "Use for every interaction with Ripwire's source repository, including read-only inspection, Git work, source and documentation changes, builds, compiler issues, installation, and skill work. Add `$manage-ripwire-skills` only for skill-related enhancements, changes, or review of proposed skill changes. Merely using the `ripwire` CLI on another repository does not trigger this skill."
---

# Manage Ripwire Repository

Apply this owner before work involving the Ripwire checkout, normally `~/github-forks/ripwire` or another explicitly selected source checkout. It applies to every task and phase, including reads, reviews, build diagnosis, installation, and skill work. Reuse a complete unchanged contract already retained in context; another symbol or status question does not require reloading it.

## Establish the repository context

Resolve the selected checkout and apply its cumulative `AGENTS.md` guidance and the full guide it designates, currently `CLAUDE.md`. Read the relevant contributor guidance before changing C++ or gates. The current checkout owns build commands, compiler requirements, install behavior, and verification; this skill does not freeze release numbers, gate counts, or old command behavior.

Keep local skill selection and workflow policy in `~/agentic-skills` and its authorized harness projections. Do not add local skill-routing rules to the Ripwire checkout's tracked `AGENTS.md`, `CLAUDE.md`, or other upstream-owned guidance. Use skill descriptions and canonical routing owners for selection so upstream pulls do not require reapplying or resetting a local guidance patch.

Preserve the user's requested phase and existing work. Applying this skill does not by itself authorize a pull, build, installation, commit, push, skill comparison, or harness change. Perform those effects when the task or an applicable standing workflow authorizes them. The canonical skill repository's Git workflow does not extend to the Ripwire checkout.

## Compose the skill owners

`$manage-ripwire-repo` always owns Ripwire repository context. Add `$manage-ripwire-skills` only when the task concerns enhancing, changing, or reviewing proposed changes to Ripwire skill definitions. The two owners compose; skill work does not replace the repository owner. A general upstream pull, compiler repair, build, or binary installation does not trigger skill comparison or port updates.

| Requested work | Owners |
| --- | --- |
| Inspect, review, change, or pull the Ripwire checkout | `$manage-ripwire-repo` plus the skill for the current task when needed |
| Diagnose a compiler failure, build, or install Ripwire | `$manage-ripwire-repo` plus the skill for the current task when needed |
| Review upstream skill enhancements or reconcile canonical skill ports | `$manage-ripwire-repo` and `$manage-ripwire-skills` |
| Enhance a canonical Ripwire skill definition | `$manage-ripwire-repo` and `$manage-ripwire-skills` |
| Use `ripwire` to analyze an unrelated repository | The navigation or task skill; this repository owner is not triggered |

`~/agentic-skills` owns the customized Ripwire skill definitions; the Ripwire checkout supplies upstream input. When working in that canonical repository, apply `$manage-agentic-skills-repo` first for its own repository workflow. Keep upstream, staged installer assets, canonical definitions, and live harness projections distinct.

When the user requests both a new tool installation and skill enhancements, finish and verify the installation before manually reconciling enhancements into the canonical ports. Successful installation alone does not start that work. An explicit skill-only task does not require an unrelated rebuild or reinstall.

## Load only the current procedure

For a build, compiler-selection failure, PGO run, or installation, read [build-and-install.md](references/build-and-install.md). For skill work, load `$manage-ripwire-skills` and only its resources required by the requested effect. Ordinary source inspection does not need either procedure.

Report the actual reached state: source revision, selected compiler and build flavor, commands and exits, resulting binary, installation destination when applicable, and any separately authorized skill work. A configured tree, built binary, installed executable, reconciled port, and activated harness link are different outcomes.
