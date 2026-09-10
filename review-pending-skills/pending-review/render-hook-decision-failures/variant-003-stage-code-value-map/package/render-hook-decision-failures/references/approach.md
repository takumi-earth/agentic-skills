# Approach contract

## Identity

- Candidate: `render-hook-decision-failures`
- Variant: `variant-003-stage-code-value-map`
- Classification: `instruction-gap`, `resource-gap`

## Required behavior

Use a compact stable stage/code/value map suitable for both human context and downstream parsing.

Emit a concise diagnostic such as stage=resolve_goal_file, code=attachments_root_mismatch, condition=..., expected=..., received=... and keep value rendering home-relative.

The default CLI preserves `additionalContext`, `diagnostic`, and `mode`. With `--hook-only`, emit only `hookSpecificOutput` containing `hookEventName: PostToolUse` and `additionalContext`. Require nonempty identifying text; expected and received accept JSON values or literal strings, including empty observations. Normalize path-bearing keys and values at home-path boundaries while preserving unrelated text and sibling identities. Reject key collisions introduced by normalization instead of overwriting a diagnostic fact.

Bound nesting to `32` child edges and reject non-finite numbers. These invalid values and malformed identifying fields produce a structured `invalid-decision-input` diagnostic, empty stderr, and exit `0`; process success does not establish decision success. Missing options and invalid command grammar retain argparse's exit `2` behavior.

Serialize the selected output with one final newline and enforce a total `8192`-byte UTF-8 budget. On overflow, replace the original diagnostic in full with `output-budget-exceeded`, the omitted context byte count, and original serialized byte size. This is a presentation omission, not a new verdict about the underlying operation. Caller-owned fact selection still determines what may be published; rendering does not authorize recording or additional channels.

## Planned resources

- `complete SKILL.md`
- `agents/openai.yaml`
- `scripts/render_hook_decision.py`
- `references/diagnostic-codes.md`

## Relationships

- `design-command-observability`: `possible-shared-foundation`
- `auto-skill-enhancer`: `current-hook-consumer`
- `resolve-managed-goal-artifacts`: `resolution-result-consumer`

Relationships preserve overlap for review. They do not authorize mutation of the named owner.

## Validation contract

- stable field ordering
- home-path normalization
- null and collection rendering
- no generic fallback when known values exist

## Git and activation boundary

Include the complete candidate root in the single creation-batch commit; never commit one renderer variant alone.

Do not promote, enable, synchronize, register, or publish this pending package without separate explicit user authority.
