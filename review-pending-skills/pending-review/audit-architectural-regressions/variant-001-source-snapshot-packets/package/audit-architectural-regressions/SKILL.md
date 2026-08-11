---
name: audit-architectural-regressions
description: "Build source-first, decision-ready architectural regression and remediation verdict packets across Git checkpoints or divergent implementations. Use when a user asks what architecture regressed between versions, which current operations violate an ownership or causal boundary, what exact remediation should be approved, or how to make the comparison repeatable. Collect complete source blobs and anchored excerpts rather than treating Git diffs, line counts, version bumps, or current implementation as architecture authority. Do not use this skill merely to summarize a diff, defer classification to the reviewer, apply remediation, change protected architecture, or infer mutation, commit, or publication authority."
---

# Audit Architectural Regressions

Produce a self-contained verdict packet that finishes the source investigation before asking the user for a decision.

## Freeze authority and checkpoints

- Read the current user decision, protected architecture, ownership ledgers, and applicable repository guidance before classifying source.
- Name the comparison baseline, intermediate checkpoints, and current source explicitly. Resolve every historical checkpoint to a commit identifier and distinguish committed `HEAD` from the working tree.
- Treat complete source at each checkpoint as evidence. Do not use a Git diff, changed-line count, dependency-version-only commit, or current implementation shape as the classification model.
- Keep evidence collection and remediation application separate. This workflow may write only explicitly requested reports and scratch evidence; it does not authorize source edits, generators, dependency commands, staging, commits, pushes, or publication.

## Collect reproducible source evidence

Read [references/source-evidence-spec.md](references/source-evidence-spec.md) before authoring the first evidence specification in a repository.

1. Put task-local specifications and generated evidence beneath the canonical skill repository's `.scratchpad/audit-architectural-regressions/<task-id>/` unless the user selected another output destination.
2. Declare every checkpoint, repository override, source path, production scope boundary, symbol or regular-expression anchor, and required context in one JSON specification.
3. Run `scripts/collect_source_evidence.py`. The collector reads worktree files or complete `git show <commit>:<path>` blobs, resolves exact line ranges, hashes each source, and emits deterministic JSON plus an unwrapped Markdown evidence appendix.
4. Read each relevant complete source file at every checkpoint when semantic classification depends on context outside the extracted range. An anchored excerpt makes the verdict reviewable; it does not replace first-hand source understanding.
5. Re-run the collector after changing a query. Never hand-edit generated evidence to make an anchor fit a conclusion.

When one finding depends on every invocation of a broad Rust structural helper, also read [references/rust-call-inventory-spec.md](references/rust-call-inventory-spec.md) and run `scripts/collect_rust_call_inventory.py`. Use its owner and identity records to embed every selector in the verdict packet; a call count plus owner names is not a completed site disposition.

```bash
python3 scripts/collect_source_evidence.py \
  --spec <source-evidence-spec.json> \
  --output-json <source-evidence.json> \
  --output-markdown <source-evidence.md>

python3 scripts/collect_rust_call_inventory.py \
  --spec <rust-call-inventory-spec.json> \
  --output-json <rust-call-inventory.json> \
  --output-markdown <rust-call-inventory.md>
```

## Finish classification before requesting a verdict

For every disputed mechanism, table row, registered job, patch operation, generated artifact, or ownership edge, record one concrete disposition:

- `keep`: retain the current operation and name the protected owner or seam that justifies it;
- `narrow`: replace the current operation with a named smaller mutation and list the exact retained target state;
- `move`: name the destination owner, the behavior that moves, and the residual wiring seam;
- `remove`: delete the operation and name any intentionally preserved diagnostic or fixture role;
- `replace`: name the successor capability, inputs, outputs, barriers, and protecting evidence;
- `blocked-by-decision`: use only for a genuine architecture choice that cannot be derived from current authority, and state the mutually exclusive outcomes.

Do not put “build a table,” “audit separately,” “inventory every site,” “classify the rows,” “find the references,” or an equivalent research task in actionable remediation. Perform that work and embed the completed table. Do not ask the user to pre-approve how an unknown result will be handled.

## Build a decision-ready finding

Make every finding independently reviewable without requiring the reader to open source or reconstruct the conversation. Include:

1. A precise verdict and scope, including what is not classified as regression.
2. Historical and current evidence with checkpoint, path, exact line range, symbol or row, source hash reference, and a short verbatim excerpt where it materially improves evaluation.
3. A complete current-operation disposition table naming the operation, location, owner, decision, exact change, retained behavior, and protecting evidence.
4. An ordered remediation sequence whose steps already embody the completed dispositions.
5. Concrete positive and negative evidence that would prove the remediation preserves the selected architecture.
6. One or more verdict units. Each unit states `Evidence`, `Change`, `Approval means`, `Rejection means`, `User verdict`, and `User comment`.

Group rows only when the packet lists every grouped member and every member has the same owner, disposition, replacement, and protecting evidence. Counts without identities are not a complete inventory.

## Validate the packet

Create a small packet contract naming every finding presented for decision, its required sections, required evidence query IDs, exact evidence inventory counts where the verdict depends on them, source-locator minimums, required strings, forbidden deferrals, and minimum verdict units. Do not contract only the first examples while later findings still contain research tasks. Run:

```bash
python3 scripts/validate_verdict_packet.py \
  --packet <regression-remediation.md> \
  --contract <packet-contract.json> \
  --evidence-json <source-evidence.json> \
  --rust-call-inventory-json <rust-call-inventory.json>
```

Require a zero exit status. The validator rejects manual prose wrapping, unresolved placeholders, missing evidence queries, changed pinned evidence counts, absent finding sections, insufficient source locators, incomplete verdict units, task-specific forbidden deferrals, and omitted stable Rust call-site keys when a finding contracts a call inventory. Validation proves packet structure and evidence linkage; it does not prove the semantic verdict.

## Hand off without applying remediation

- Lead with the exact findings and concrete verdict units now ready for review.
- Link the packet, source-evidence JSON, evidence appendix, and packet contract.
- State which claims remain interpretive and which source facts are machine-collected.
- State every command, mutation, verification, commit, or activation effect that remains unauthorized.
- Stop after the user can approve, reject, or question each exact remediation unit without beginning a new investigation.
