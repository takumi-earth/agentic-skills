---
name: commit-strict-work
description: "Execute low-freedom commit workflows for `strict*` ecosystem repositories. Use only when the user explicitly asks to commit, author a commit message, commit what is staged, preserve staged-versus-unstaged state, use `--no-verify`, or follow a hook-specific commit protocol. This skill does not authorize staging, unstaging, verification, pushes, history repair, or worktree inspection beyond the user's exact request."
---

# Commit Strict Work

The user owns commit timing, content, index state, hook behavior, and publication. Execute the exact protocol without normalizing the repository.

## Classify the request

Extract:

- whether the task is message-only or an actual commit;
- whether the target is the current index, named files, or implementation work from the current task;
- whether unstaged state may be read;
- whether staging or unstaging is authorized;
- whether hooks must run or `--no-verify` is required;
- whether verification is authorized;
- whether amend, push, branch, or remote operations are authorized.

Do not commit before explicit go-ahead. A plan, completed implementation, or green gate is not commit authority.

## Use the staged-only protocol

When the user says `staged`, `staged-only`, `commit what is staged`, or `do not look at unstaged`:

1. Inspect only cached/index material needed to understand the commit, such as `git diff --cached --name-status`, `git diff --cached --stat`, `git diff --cached`, or cached file content.
2. Do not run `git status`, ordinary `git diff`, worktree scans, log, remote inspection, or commands that reveal unstaged state.
3. Do not stage, unstage, restore, reset, checkout, clean, stash, or otherwise normalize the index/worktree split.
4. Do not exclude or add a path because it appears pre-existing, unrelated, generated, or inconvenient. The current staged set is the user-owned scope.
5. Do not run verification when it is prohibited or when `--no-verify` is required.
6. Commit exactly the index.
7. Report the commit hash and cached/index state only; make no claim about the unseen worktree.

A remote, branch, or topology concern does not block a locally executable commit unless the commit itself requires an unauthorized mutation.

## Preserve product framing

Derive the change hierarchy from authorized content:

1. Identify the repository's product crate or behavioral deliverable.
2. Lead with structural product/API/runtime behavior.
3. Treat automation, template wiring, policy files, lockfiles, badges, coverage, generated metadata, and renames as support unless they are the product.
4. Read enough authorized staged content to describe behavior accurately.
5. Never guess module behavior from filenames or narrate tool mechanics as the main change.

## Use the required message structure

Unless the user explicitly overrides it for this commit:

- Subject: `type(scope): structural imperative description`.
- Always include a scope.
- Never use `chore`.
- Append `!` for a breaking change.
- Use imperative mood and describe the structural change.
- Use `1`–`5` body sections proportionate to the commit.
- Give each section a plain-text header, never a Markdown heading or bold text.
- Put `3`–`5` imperative structural bullets under each section.
- Separate sections with exactly one blank line.
- Pass the message to `git commit -m` with a HEREDOC so spacing survives shell quoting.

Do not pad a small commit or compress a broad change into one vague section.

## Handle hooks and fallout

- Use `--no-verify` exactly when requested.
- Otherwise, do not silently bypass requested hooks.
- If a hook mutates generated or unrelated tracked artifacts, report the fallout. Do not absorb, restore, stage, or recommit it without authority.
- If the hook fails, report the exact failure and current commit state. Do not broaden implementation or verification scope automatically.
- Do not amend, retry with a different message, or change hook policy unless authorized.

## Report the outcome

State:

- commit hash and subject;
- whether hooks ran or were skipped as requested;
- whether the cached/index set is empty or still contains entries, using cached-only evidence when worktree inspection is prohibited;
- any hook-generated fallout or blocker visible within the authorized boundary;
- that no push occurred unless the user explicitly requested and authorized one.
