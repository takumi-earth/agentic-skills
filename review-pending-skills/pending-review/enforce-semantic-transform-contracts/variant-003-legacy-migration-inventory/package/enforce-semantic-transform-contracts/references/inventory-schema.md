# Legacy transformation inventory schema

The scanner emits JSON with this shape:

```json
{
  "schema_version": 1,
  "roots": ["src"],
  "sites": [
    {
      "site_key": "src/patch.rs:42:fixed-path",
      "path": "src/patch.rs",
      "line": 42,
      "signals": ["fixed-path", "whole-body"],
      "owner": "unassigned",
      "disposition": "review",
      "review_state": "signal-only",
      "excerpt_hash": "sha256:..."
    }
  ]
}
```

## Signal classes

- `fixed-path`: a source-file path appears near transformation dispatch.
- `marker-gate`: a text marker can prevent authoritative discovery.
- `whole-body`: a complete item or large replacement body appears embedded.
- `fingerprint` or `hash`: exact token or byte identity appears in applicability logic.
- `regex-target`: a regular expression identifies source structure.
- `text-fallback`: textual replacement or matching appears after structured discovery fails.

Signals are lexical review leads, not defect verdicts. The scanner groups multiple signals at the same line, sorts by repository-relative path and line, and derives `site_key` from location and signal class within one source snapshot. Unrelated line insertion changes the key; it is not a stable identity across a migration. Owners and dispositions default to `unassigned` and `review`; reviewers may enrich a downstream ledger without modifying source.

Never feed an excerpt hash or site key back into transformation applicability.

The report includes `files_scanned`, `line_model: "LF"`, and `excluded_symlinks`. Successful completion covers the selected roots under the declared suffix filter, not all transformation behavior. Overlapping roots share one scan per path. File and directory symlinks are excluded, and an explicitly selected symlink root is rejected. Missing, unreadable, non-UTF-8, escaping, or invalid roots produce a structured error and exit `2`, never an empty successful inventory. File hashes identify the original bytes that supplied each line anchor.

Supported suffixes are `.rs`, `.py`, `.ts`, `.tsx`, `.js`, and `.jsx`; `.git` directories are excluded during directory traversal. Paths are repository-relative in reports, and operational errors use `~/...`. Selection checks do not promise an immutable filesystem snapshot under concurrent mutation. Persistence remains optional under the task's artifact contract.
