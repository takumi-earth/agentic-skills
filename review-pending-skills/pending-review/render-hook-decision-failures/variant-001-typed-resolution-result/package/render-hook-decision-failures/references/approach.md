# Approach contract

## Identity

- Candidate: `render-hook-decision-failures`
- Variant: `variant-001-typed-resolution-result`
- Classification: `instruction-gap`, `resource-gap`

## Required behavior

Return a typed success-or-failure result from each policy decision and render it once at the hook boundary.

Model `status`, `stage`, `code`, `condition`, `expected`, `received`, `candidate_count`, and optional `artifact` as explicit fields. Keep success and failure mutually exclusive. Require nonempty diagnostic text, accept only bounded domain-selected values, normalize home paths, and serialize only a valid Codex `PostToolUse` envelope.

The seven required fields exclude `artifact`; unknown fields are invalid. Optional `artifact` accepts nonempty text or `null`, and optional `approach` accepts nonempty text. Required `expected` and `received` accept finite JSON values, including empty strings and collections. Diagnostic strings are limited to `512` characters, object keys to `64` nonempty characters, collections to `16` entries, and child values to four nesting edges. Strings and keys permit tab, carriage return, and newline but reject other control characters below `U+0020`. Identifying text must contain a non-whitespace character. `candidate_count` is a nonnegative integer, including integral JSON number spellings such as `1.0`, and never a Boolean.

Normalize path-bearing keys and values without changing sibling paths or unrelated text. If normalization would collapse two object keys, report a safe presentation failure rather than discarding a fact. This check depends on the current home directory and supplements the portable schema. Invalid input contents are withheld; value validation alone does not prove redaction.

Limit the complete emitted JSON and final newline to `8192` UTF-8 bytes. Oversized valid decisions retain their reported success or failure but replace the context with an explicit full-omission notice, omitted context byte count, original serialized byte count, and renderer code `output-budget-exceeded`. The renderer does not replace goal-specific completion accounting, delimiters, or the write-and-re-read barrier.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `scripts/render_hook_decision.py`
- `references/decision-result-schema.json`

## Relationships

- `design-command-observability`: `possible-shared-foundation`
- `maintain-living-goal`: `canonical-owner`
- `resolve-managed-goal-artifacts`: `upstream-result-source`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- one exact fixture for every failure code
- success path contains no failure language
- stdout remains one valid `PostToolUse` JSON object and stderr remains empty
- identifying text is nonempty and expected/received observations are present, including legitimate empty values
- malformed and unsafe input renders a bounded generic diagnostic

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit; never commit one renderer variant alone.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
