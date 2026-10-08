# Agentic Skills Repository

## Repository Git workflow

- Use `$manage-agentic-skills-repo` first whenever an agent works in this repository, for any reason. If the synchronized skill is unavailable, read its [canonical `SKILL.md`](manage-agentic-skills-repo/SKILL.md) directly.
- Pull before task-specific reads, research, planning, review, validation, or edits. Read the minimum applicable guidance and coordinate overlapping work first; reuse the successful pull within the same task.
- After making changes, run `git add .` from the Git top-level, commit the complete uncommitted repository scope, and push to the configured upstream. Include pre-existing, unrelated, and unfamiliar changes. Read all staged diffs and make the commit message reflect every material change group.
- Pulling, integrating committed history, staging, committing, and pushing this repository have standing user authorization. Do not ask again for these effects or merely because some changes were made by someone else. Follow the shared skill to resolve incoming changes while preserving history and file contents. A current explicit user instruction for the task, such as a staged-only request or command ban, takes precedence. Other enablement remains separately authorized.

## Purpose and authority

- Treat this repository as the canonical source for the user's user-level skills across machines, operating systems, agent harnesses, and model providers.
- Apply these conventions from the repository's first commit onward. An empty or short Git history does not imply that naming, validation, distribution, or commit conventions are undecided.
- Treat installed harness copies as deployment targets, not independent sources of truth. Make durable changes here and then distribute them through the appropriate harness workflow.
- Preserve one semantic skill contract wherever harnesses can share it. Isolate genuinely harness-specific metadata or controls instead of maintaining silently divergent copies of the same skill.

## Repository layout

- A deployable skill is an immediate child directory whose root contains `SKILL.md`.
- `SKILL.md` is the canonical skill identity, trigger description, and instruction body. Its frontmatter `name` must match the package directory name unless an external harness specification explicitly requires otherwise.
- `agents/openai.yaml` contains OpenAI-facing interface metadata when that harness surface is supported. Keep its `$<skill-name>` prompt reference aligned with the canonical `SKILL.md` name.
- Put executable helpers in `scripts/`, selectively loaded supporting guidance in `references/`, and reusable output material in `assets/`. Keep resource references relative to the skill package whenever possible.
- `.skill-specs/` is external, reference-only material. It is not a skill package and must never be copied, linked, enumerated, or installed into a harness as one.
  - `.skill-specs/ext/` is the pinned upstream `agentskills/agentskills` submodule. Do not edit its contents as local source; update the submodule pointer deliberately when an upstream refresh is requested.
  - `.skill-specs/references/` contains local reference material used to interpret skill format and design guidance. Changes there are reference maintenance, not skill deployment.
- `.scratchpad/` is the repository location for task-required transient work and durable workflow evidence; it is not authority to create either. Create an artifact only when the user-requested deliverable or an already-authorized mutation, recovery, or handoff workflow intrinsically requires persistence. Ordinary source reads, status checks, narrow diagnosis, validation, completion reasoning, and continuation do not require a task-local report merely because their output may be mentioned later.
- Preserve task deliverables at an explicitly user-selected external destination when that destination is part of the task contract. This is distinct from skill scratch output: diagnostics, fixtures, and workflow bookkeeping still belong under the canonical repository's `.scratchpad/`.
- `.scratchpad/` is not deployable content. Keep its artifacts out of skill-package allowlists and harness synchronization. Prefer one current artifact for each explicitly required gate. Preserve historical audit versions only when the task contract requires an audit trail; do not create numbered revisions merely to restate, strengthen, or reclassify unchanged evidence.
- `CLAUDE.md` is a compatibility pointer to this file. Keep durable repository guidance in `AGENTS.md` rather than duplicating it by harness.

## Distribution boundary

- Select deployable packages positively: install only immediate child directories containing a root `SKILL.md`.
- Do not install by recursively copying the repository root. That would leak `.skill-specs/`, `.scratchpad/`, Git metadata, repository guidance, and other non-package files into harness skill roots.
- Preserve the whole selected package, including its `scripts/`, `references/`, `assets/`, and harness metadata. Do not deploy only `SKILL.md` when the body depends on packaged resources.
- Exclude hidden directories and non-skill top-level directories even if they contain nested `SKILL.md` files. Nested examples or upstream fixtures do not become user-level skills by discovery accident.
- When a harness needs a different metadata schema, translate only the interface layer. Do not change the underlying behavioral contract merely to fit one harness's discovery mechanism.
- Prefer package-relative paths and documented harness variables over checkout-specific absolute paths. Retain an absolute path only when it is an intentional part of the skill's behavior, and make the portability boundary explicit.

## Editing a skill

1. Read the target `SKILL.md` completely before editing it.
2. Read every directly referenced instruction file needed for the requested behavior, plus any script or metadata file that the change can affect.
3. Identify the existing semantic owner and trigger boundary. Extend that owner when the behavior belongs there; create a separate skill only when the trigger or responsibility is genuinely distinct.
4. Keep `SKILL.md` focused on information an agent would not reliably infer. Move conditional detail into a named resource and state exactly when to load it.
5. Preserve explicit authorization boundaries. A review or proposal does not authorize implementation, and a skill edit does not authorize adjacent hooks, configuration, memory, installed copies, or external changes. Apply this repository's standing pull, commit, and push workflow separately; it does not authorize Git effects in other repositories.
6. Update `agents/openai.yaml` when the skill name, invocation-facing description, default prompt, implicit-invocation policy, or other OpenAI interface behavior changes. Do not regenerate it for a body-only change that leaves the interface contract intact.
7. Treat scripts as product code. Keep deterministic logic in scripts when it is more reliable than prose, route their scratch and generated output through the resolved repository `.scratchpad/`, and test every added or changed executable path directly.
8. Make surgical edits. Preserve unrelated user changes and do not normalize neighboring packages merely because they are present.

## Skill design conventions

- Write trigger descriptions that say both when to use the skill and when not to use it when overlap is plausible.
- Prefer one coherent responsibility over a broad collection of loosely related instructions.
- Use progressive disclosure: keep core decisions in `SKILL.md` and load detailed references only at their actual trigger point.
- Keep reference chains shallow. A referenced file should not force an agent through an undocumented maze of further references.
- Give fragile workflows exact ordering, stop conditions, and validation. Give judgment-heavy work clear invariants and ownership boundaries rather than brittle scripts of prose.
- Use examples as reusable patterns, not as hard-coded answers to one historical task.
- Preserve accepted user requirements when correcting diagnostics. An implementation-derived assertion is fallible evidence, not an additional requirement. Before changing an acceptance predicate or normal tool behavior, identify the protected property, its authority, a permitted variation, and a forbidden effect. Correct false rejection at its owner while retaining evidence against the forbidden effect; do not force healthy tools to satisfy an unsupported predicate. `$guard-strict-work` owns the conditional provenance procedure and `$verify-strict-work` owns acceptance evidence.
- Do not use generated output, negative fixtures, static exclusions, lint allowances, or harness-specific quirks as automatic exceptions. Document a narrow compatibility boundary only when the user explicitly authorizes it.

## Validation

- Validate every changed skill directory with the canonical validator available in the target environment. The pinned base specification documents `skills-ref validate ./<skill-name>`; harness-specific metadata may require an additional harness validator.
- Treat `.skill-specs/` as validator/reference input only. A validation workflow must not package it or mutate the pinned submodule to make a skill pass.
- Run direct tests for every changed script. Use the package's existing test entry point rather than inventing a substitute audit.
- Forward-test meaningful trigger or workflow changes with realistic positive and negative prompts when the behavior cannot be established by structural validation alone.
- Distinguish helper tests from agent behavioral evaluations. Behavioral claims require actual tool traces and observed effects; matching instruction text or a model's promised behavior is insufficient. Test retained authorization through corrections as well as unauthorized expansion.
- Report assertions and process exit status separately. A command with successful inner checks but a nonzero final status is not a passing gate.
- If a required validator cannot run because of permissions, temp-directory access, cache access, sandboxing, or network restrictions, rerun the intended command with the harness's escalation mechanism. Do not redirect caches or temporary directories to change command behavior.
- Do not claim repository-wide validation when only selected packages were checked. Name the exact packages, scripts, commands, and outcomes.

## Worktree discipline

- Treat a dirty worktree as a merge-safety condition, not a reason to reduce scope, weaken design, skip expected generated outputs, or replace a real command with a check-only variant.
- Preserve unrelated file contents. Do not revert or overwrite them. The standing `$manage-agentic-skills-repo` workflow includes their changes in the complete repository commit after task changes.
- If a file in scope is already modified, read and edit its current contents instead of assuming the index or `HEAD` version is authoritative.
- Follow the standing repository pull and complete stage/commit/push instruction after task changes. Do not independently unstage, restore, reset, force-push, or rewrite history without explicit authority.
- When implementation formatting exists, run the repository's real formatting command. Do not substitute `--check` merely because the tree is dirty.
- Report incidental changes made by legitimate repository commands plainly; do not hide or silently discard them.

## Agent and harness behavior

- Do not delegate ordinary work unless the user explicitly asks for subagents, agents, delegation, waves, orchestration, parallel work, or a full-history fork.
- When delegation is requested, give each worker the full available context and a self-contained assignment naming its objective, owned paths, forbidden edits, sibling constraints, verification, stop conditions, and final report fields.
- Keep worker assignments single-purpose. Reuse a worker only for clarification, correction, or continuation of the same slice; use a fresh worker for an unrelated topic.
- Keep final ownership, cross-package consistency, and acceptance decisions with the primary agent.
- Preserve proper Markdown backticks around literal commands, paths, identifiers, configuration, prompts, and technical wording in all repository-facing responses and artifacts.
- Do not hardwrap content. Keep prose paragraphs, list items, and literal commands on one logical line; use line breaks for actual document or code structure.

## Commit convention

- The standing `$manage-agentic-skills-repo` instruction explicitly requires a complete repository commit and upstream push after task changes. Other repositories' Git workflows require their own explicit authority; current user instructions can narrow or override this repository default.
- Use the subject form `type(scope): structural imperative description`.
- Always include a scope. Never use `chore`; choose the structural type that describes the change, such as `feat`, `fix`, `refactor`, `build`, `ci`, `docs`, `test`, or `style`.
- Add `!` before the colon for a breaking change, for example `feat(distribution)!: replace copied skills with package selection`.
- Write the description in imperative mood and name the structural change rather than the work narrative.
- Use one to five body sections according to the commit's actual breadth. Each section starts with a plain-text header and contains three to five imperative bullet items describing introduced, replaced, removed, renamed, or rewired structure.
- Separate body sections with exactly one blank line. Do not use Markdown headings, bold text, or underlines for section headers.
- Pass the complete message to `git commit -m` through a HEREDOC so blank lines and bullet spacing are preserved.
- For staged-only requests, inspect only the index and preserve all staged-versus-unstaged splits exactly. Do not stage adjacent work or inspect forbidden worktree content to improve the message.
