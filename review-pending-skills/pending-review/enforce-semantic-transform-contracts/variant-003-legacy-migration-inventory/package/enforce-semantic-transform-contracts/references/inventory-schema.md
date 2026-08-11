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

Signals are lexical review leads, not defect verdicts. The scanner groups multiple signals at the same line, sorts by repository-relative path and line, and derives `site_key` only from stable location and signal class. Owners and dispositions default to `unassigned` and `review`; reviewers may enrich a downstream ledger without modifying source.

Never feed an excerpt hash or site key back into transformation applicability.
