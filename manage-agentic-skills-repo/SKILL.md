---
name: manage-agentic-skills-repo
description: Pull the canonical agentic-skills repository before every task and, after making changes, stage and commit all uncommitted repository changes with a message reflecting the complete diff. Use first whenever an agent works in this repository for any reason, including reading, research, planning, review, validation, skill editing, and maintenance. Do not apply these Git effects to other repositories or installed skill copies.
---

# Manage Agentic Skills Repository

Apply the user's standing repository workflow: pull first; after making changes, run `git add .` from the repository root and commit everything that remains uncommitted. Include pre-existing, unrelated, and unfamiliar changes. This instruction supplies refresh, staging, and commit authority for this repository without another permission request. A current explicit user instruction for the task takes precedence, including a staged-only request or a command ban.

## Pull before every task

1. Resolve the canonical source checkout, using an explicitly selected checkout, `AGENTIC_SKILLS_REPO`, or `~/agentic-skills`. Resolve package symlinks to their source; an installed copy is not the repository. Confirm the Git top-level, current branch, configured upstream, and any unfinished Git operation. Read the minimum applicable guidance and coordinate overlapping work with reachable existing agents before Git effects.
2. Make the pull the first repository workflow action, before task-specific source reads, analysis, validation, or edits. Reading, planning, and review still require it. From the canonical Git top-level, run:

   ```bash
   git pull --ff-only --no-rebase --no-autostash
   ```

3. Preserve local commits, index entries, and file contents. Let Git keep compatible local work and refuse an obstructed fast-forward. A detached checkout, missing upstream, unfinished merge or rebase, divergent history, or failed pull stops dependent task work. Report the actual failure; do not stash, reset, clean, change tracking, rewrite history, or continue with a stale checkout to make progress. For sandbox, permission, cache, temporary-directory, or network restrictions, request escalation for the same command and wait for approval.
4. If incoming commits change applicable guidance, this skill, another selected skill, or its required resources, read their refreshed bodies completely before continuing. Apply the refreshed contract without recursively restarting the successful pull. Reuse that pull during the same task and retained-context continuations; start a new task with a new pull.

A task that makes no local file changes still pulls first. Existing dirt alone does not require a commit during otherwise read-only work. A fast-forward imports already committed history and does not itself require a new commit.

## Commit the complete repository after changes

Complete the user's requested changes and applicable formatting or validation first. Creating, editing, deleting, or generating repository files triggers this conclusion, including legitimate command fallout. Preserve unrelated file contents while including their changes in the commit.

1. Work from the verified Git top-level, even if the task was performed inside one skill directory. Stage the complete normal repository scope with the exact command:

   ```bash
   git add .
   git diff --cached --name-status
   git diff --cached --stat
   git diff --cached --no-ext-diff --no-textconv
   ```

2. Include all staged and unstaged changes captured by `git add .`: pre-existing edits, unfamiliar edits, new files, deletions, and changes made by other agents. Do not restrict the commit to your own paths, preserve an earlier partial staging split, or request confirmation merely because an edit is unrelated or unfamiliar. Keep Git-ignored files ignored; do not force-add scratch evidence or independently commit changes inside a submodule.
3. Read every included diff before authoring the message. If output is truncated, continue with bounded file-specific reads until the complete staged scope has been reviewed. Inspect new-file contents and relevant binary or submodule evidence as needed. Describe observed structural changes accurately without inventing intent or claiming authorship of unfamiliar work. A diff inventory or summary of your own edits is insufficient.
4. Follow the repository's `AGENTS.md` commit convention: a scoped conventional subject in imperative mood, no `chore`, and proportionate plain-text body sections with imperative bullets. Cover every material change group in the staged diff. Pass the message through a quoted HEREDOC so literal backticks, dollar signs, and newlines survive:

   ```bash
   git commit -m "$(cat <<'COMMIT_MESSAGE'
   <type>(<scope>): <structural imperative description>

   <Plain-text section header>
   - <Imperative structural change>
   - <Imperative structural change>
   - <Imperative structural change>
   COMMIT_MESSAGE
   )"
   ```

5. Use normal commit hooks unless the user explicitly directs otherwise. A hook failure is a failed commit; resolve it within the authorized task or report the blocker. If hooks change files, repeat `git add .`, review the complete updated diff, and update the message before retrying. When the complete staged scope is empty, report that no new commit was needed; do not create an empty commit.
6. Confirm the resulting commit and inspect remaining index/worktree changes. Finish any remaining authorized task changes with the same complete stage, review, and commit sequence; coordinate active overlapping edits before another commit. Report actual remaining changes instead of claiming a clean repository from an empty index alone.

Report the pull result, commit hash and subject, all material change groups included, validation actually performed, and remaining repository changes. Pushes, harness synchronization, installation, link creation, hook registration, and effects in other repositories require their own authority. A separately authorized workflow such as `$upgrade-codex-patch` retains its publication requirements after this skill's commit step.
