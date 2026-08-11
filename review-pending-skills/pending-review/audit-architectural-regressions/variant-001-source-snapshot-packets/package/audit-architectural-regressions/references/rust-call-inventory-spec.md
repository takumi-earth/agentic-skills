# Rust call-inventory specification

Use the Rust call-inventory collector when a finding depends on every invocation of a broad structural helper, not merely the number of matching calls. The collector masks Rust comments and literals, parses balanced call arguments, binds each call to the nearest configured owner function, and records selected identity arguments.

Use schema version `1`:

```json
{
  "schema_version": 1,
  "source": "~/work/repository/src/jobs.rs",
  "scope_end_pattern": "(?m)^#\\[cfg\\(test\\)\\]",
  "owner_pattern": "(?m)^fn (?P<owner>patch_[a-z0-9_]+)\\s*\\(",
  "calls": [
    {
      "callee": "replace_item_fn_if_needed",
      "identity_args": [3],
      "identity_labels": ["function"]
    },
    {
      "callee": "replace_trait_impl_method_if_needed",
      "identity_args": [1, 2, 3],
      "identity_labels": ["trait", "self_type", "method"]
    }
  ]
}
```

- `source` may be absolute or relative to the specification. Home paths are normalized to `~/...` in output.
- `scope_end_pattern` is optional. Use it to exclude an in-file test module when production call count is the contract.
- `owner_pattern` must define a named `owner` capture and must match the function declarations that own the reviewed calls.
- Each `callee` is matched only in executable Rust code; occurrences in comments, ordinary strings, raw strings, and the callee's own function definition are excluded.
- `identity_args` contains zero-based top-level call-argument indexes. `identity_labels` gives those arguments stable names in JSON and Markdown output.
- The collector preserves the raw identity expression with whitespace normalized. This permits literal selectors, dynamic selector variables, and composite selector expressions without pretending to evaluate Rust.
- Each record also carries a stable `site_key` formed from the enclosing owner and ordered identity arguments, such as `patch_one::function=first` or `patch_two::trait=Trait;self_type=Type;method=method`. Literal string quotes are removed in the key; dynamic selector expressions remain intact.
- A missing owner, missing requested argument, duplicate callee specification, unbalanced call, or missing requested scope boundary is an error.
- Two calls that resolve to the same stable site key are an error. Add another discriminating identity argument, such as a selector marker, rather than accepting an ambiguous inventory.

Run:

```bash
python3 scripts/collect_rust_call_inventory.py \
  --spec <rust-call-inventory-spec.json> \
  --output-json <rust-call-inventory.json> \
  --output-markdown <rust-call-inventory.md>
```

Use the generated call count, owner count, owner names, line anchors, identities, and stable site keys to complete the report's disposition table. Do not make the reader consult the generated appendix to learn the verdict; embed every stable site key and its disposition in the decision packet.
