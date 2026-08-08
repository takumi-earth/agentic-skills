---
name: verify-strict-work
description: "Preserve the exact verification contract for `strict*` ecosystem work. Use whenever a task mentions or implies testing, linting, formatting, CI, coverage, mutation testing, duplicate detection, audits, snapshots, generated checks, runtime matrices, acceptance gates, “green,” “clean,” “verify,” a verification ban, or the user's intent to run verification themselves."
---

# Verify Strict Work

Treat verification as an explicit authorization and acceptance protocol. More commands, broader scope, longer timeouts, or substitute evidence are not automatically safer.

## Extract the verification ledger

Before running a command, record:

- who owns verification;
- permitted and prohibited command categories;
- exact canonical commands and order;
- working directory, packages, features, filters, configurations, and runtime versions;
- whether formatting, generation, mutation, network, Git, or external services are separately authorized;
- pass criteria, expected duration, baseline, timeout, and stop condition;
- whether a focused command is diagnostic only or an acceptance gate;
- allowed repair scope if verification exposes unrelated failures;
- failure iteration policy: whether the batch continues after a nonzero result or stops immediately, how corrections are batched, and the exact restart point.
- post-format evidence policy: which symbol, stale-vocabulary, or reachability scans must be repeated after formatting shifts lines or names.

A command written in a plan is not authorization to run it. Implementation authority is not verification authority.

Treat a baseline as already-established timing or behavior evidence. Do not create a historical checkout, archive, revert, or provenance comparison merely to decide whether a current failure is “pre-existing” unless the user explicitly requests baseline attribution. Classify current findings by authorized scope and structural owner, not by age.

Treat Git inspection like every other verification mechanism: honor the current purpose-scoped authorization. A general prohibition remains active, while a later explicit request may authorize a named diff audit only for that audit.

## Respect bans semantically

If verification is prohibited or reserved to the user:

- Do not run focused tests, lint commands, format checks, metadata probes, mutation tools, or “cheap gates.”
- Do not replace commands with broad `rg`, `awk`, `find`, source audits, reachability scans, or manual completeness proofs.
- Do not claim correctness, cleanliness, reachability, or acceptance.
- Report implementation state and request or await the user's evidence.

Narrow source inspection required to implement a known edit is not verification. Inspection intended to prove absence, completeness, or correctness is.

## Use the canonical surface exactly

- Verify a closed snapshot. Do not audit while a dependent implementer can still edit, has pending fixes, lacks its required handoff, or has not completed its worker gates.
- When the user defines an immutable iterative ledger, run every authorized command in the batch in the declared order without source edits between commands, even after an early failure. Preserve and adjudicate the complete result set, apply the full owned correction set, and only then begin the next batch.
- When the ledger instead stops on the first nonzero result, preserve the complete known diagnostic set, leave verification, apply the full authorized correction set, and restart at the ledger's first command only after no known issue remains. Do not alternate one local fix with one gate rerun or broaden repair beyond the authorized scope.
- When one run reports several independent failures, enumerate every failure and resolve the complete authorized set before rerunning any gate. Do not use a quick rerun to discover the next item from an already-known batch.
- Run the repository-owned command rather than a raw substitute when one exists.
- Run the normal formatter for implementation work; do not use `fmt --check` merely because the tree is dirty.
- Run required symbol and stale-vocabulary scans after formatting, not before it, so shifted lines and renamed symbols cannot invalidate the evidence silently.
- Do not narrow or broaden packages, features, paths, configs, reporters, reruns, randomization, coverage, or timeout policy without approval.
- Do not introduce sharding, process isolation, alternate configs, exclusions, or acceptance-policy changes to make a gate pass.
- Test the primary supported runtime first. Test a compatibility floor separately after primary behavior is healthy.
- Treat each supported configuration independently when the matrix exists to reveal configuration-specific failures.
- Coordinate shared target directories and long-running tools with active user or agent work.
- Run verification output unfiltered. Let the harness retain oversized output; do not redirect stdout or stderr to a scratch file merely to reread it.
- Use a command's native artifact-writing option when the artifact is part of the contract. Do not synthesize reports, summaries, or snapshots with shell redirection.

## Separate diagnostics from acceptance

A focused nonzero command is diagnostic evidence even when its test assertions say `N pass, 0 fail`.

Report independently:

- assertions or test cases;
- process exit status;
- policy thresholds;
- artifact generation;
- canonical gate status.

Do not call exit code `1` passing, successful, clear, or green. Do not call focused checks equivalent to an unrun top-level gate. Worker or verifier summaries are not proof without the underlying authorized artifact or command result.

## Handle long-running commands

Before a command expected to exceed `10m`, state:

- why it is necessary;
- the evidence-backed expected duration;
- what output or condition ends it;
- the user-visible checkpoint.

Stop and ask before an interactive verification command exceeds `15m` or twice its known baseline. Do not exceed `30m` cumulative long-running verification without an explicit user checkpoint.

Do not turn a timeout into a larger timeout by default. First compare primary-runtime isolated and aggregate behavior, inspect lifecycle/resource ownership and contention, and treat runtime above twice a known healthy baseline as a performance failure even when assertions eventually pass.

Do not send more than two consecutive liveness-only updates. CPU, RSS, process existence, or a progress marker proves liveness, not health or correctness.

## Treat findings as evidence, not authority

When a gate exposes a failure:

- Classify it against the authorized implementation scope.
- Trace diagnostics to their structural owner.
- Do not silently repair unrelated findings or relax policy.
- Stop and report when repair requires a new repository, public API, compatibility decision, or user-owned policy choice.
- Preserve command fallout rather than redesigning the gate to hide it.

## Completion language

Use precise outcomes:

- “Implementation complete; verification not authorized.”
- “Focused diagnostic passed; canonical gate not run.”
- “Assertions passed; command exited `1` because the coverage threshold failed.”
- “Canonical `just ci` passed with the requested matrix.”
- “Gate blocked by an external dependency after the authorized command.”

Never infer a broader state than the exact authorized evidence supports.
