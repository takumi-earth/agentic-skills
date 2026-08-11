# Source evidence and packet contract

## Source-evidence specification

Use schema version `1`:

```json
{
  "schema_version": 1,
  "repository": "~/work/repository",
  "checkpoints": [
    {"id": "baseline", "revision": "92678bf"},
    {"id": "current", "revision": "WORKTREE"},
    {"id": "parent-current", "revision": "WORKTREE", "repository": "~/work/parent-repository"}
  ],
  "queries": [
    {
      "id": "dependency-authority-current",
      "checkpoint": "current",
      "path": "src/integrate.rs",
      "patterns": ["ROOT_WORKSPACE_DEPENDENCY_VERSIONS", "normalize_workspace_dependency_ownership"],
      "scope_start_pattern": "^fn manifest_patch_inventory_jobs",
      "scope_end_pattern": "^#\\[cfg\\(test\\)\\]",
      "context_before": 2,
      "context_after": 6,
      "required": true
    }
  ]
}
```

- Use unique checkpoint and query IDs.
- A checkpoint may set `repository` when one packet must compare source authorities from more than one Git repository. The top-level repository remains the default for checkpoints that omit it.
- Use `WORKTREE` only when current uncommitted source is intentionally part of the evidence. Every other revision resolves to a commit before capture.
- Keep paths repository-relative, forward-slash separated, and free of `..` components.
- Use regular expressions that identify semantic rows, symbols, or registration entries. Avoid line numbers as input because line numbers are collector output.
- Use `"match_mode": "source"` when one regular expression must span lines or expose named capture groups for a repeated constructor or table row. The default `line` mode matches each source line independently.
- Use `scope_start_pattern` and `scope_end_pattern` to bound a production inventory before matching, such as excluding an in-file `#[cfg(test)] mod tests` section. A missing requested boundary is an evidence error, and the generated record includes the resolved scope line range.
- Set `required` to `true` for evidence that must exist; a missing required match fails collection.
- Increase context only enough to make the operation understandable. Read the complete blob separately for semantic classification.

## Packet contract

Use schema version `1`:

```json
{
  "schema_version": 1,
  "require_unwrapped_prose": true,
  "forbidden_phrases": ["build an explicit review table", "audit separately"],
  "findings": [
    {
      "id": "R1",
      "required_sections": ["Verdict", "Historical and current evidence", "Completed operation disposition", "Actionable remediation", "Required evidence", "Remediation verdict"],
      "required_evidence_queries": ["dependency-authority-current"],
      "evidence_assertions": [
        {"query_id": "dependency-authority-current", "match_count": 2, "capture_count": 2, "pattern_capture_counts": {"0": 1, "1": 1}}
      ],
      "required_strings": ["`dependency-authority-current`"],
      "minimum_source_locators": 3,
      "minimum_verdict_units": 1,
      "rust_call_inventory": {
        "source": "~/work/repository/src/jobs.rs",
        "call_count": 2,
        "owner_count": 2,
        "require_site_keys": true
      }
    }
  ]
}
```

- Scope every contract to findings that are expected to be decision-ready in the current packet.
- List task-specific deferrals in `forbidden_phrases`; matching is case-insensitive.
- Use exact subsection titles in `required_sections`.
- Cite each required evidence query ID literally in the finding.
- Contract every finding that is presented as decision-ready; do not validate only the first examples while later findings still delegate source classification to the reviewer.
- Use `evidence_assertions` to pin source-derived `match_count`, `capture_count`, or exact `pattern_capture_counts` when a verdict depends on an inventory total. A later source change must fail validation until the evidence and disposition are reviewed again.
- A source locator is a backticked `path:line` or `path:start-end` reference, optionally prefixed by a checkpoint and colon.
- Each verdict-unit heading must be a fourth-level heading containing a backticked ID such as `R1-A`.
- Each verdict unit must contain bold labels for `Evidence`, `Change`, `Approval means`, `Rejection means`, `User verdict`, and `User comment`.
- Keep `User verdict` values explicit, such as `approve / reject / question`; do not use underscore blanks or `TBD` markers.
- When `rust_call_inventory` is present, pass the generated inventory with `--rust-call-inventory-json`. The validator pins its source, call count, owner count, and—when `require_site_keys` is true—requires every stable call-site key to appear inside that finding.
