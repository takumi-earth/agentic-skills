# Metamorphic fixture model

The generator consumes one JSON object:

```json
{
  "schema_version": 1,
  "fixture_id": "add-timeout-hook",
  "scope": ["crate-a/src"],
  "owner": "crate-a::Client::send",
  "target": {
    "file": "crate-a/src/client.rs",
    "module": "client",
    "node_id": "send-call",
    "pre_state": {"operation": "send", "timeout": false},
    "post_state": {"operation": "send", "timeout": true}
  },
  "unrelated": [{"node_id": "decoy-send", "owner": "crate-a::Tests::send"}],
  "permitted_move": {
    "file": "crate-a/src/http/client.rs",
    "module": "http::client"
  },
  "drift_state": {"operation": "dispatch", "timeout": false}
}
```

The output is a sorted JSON case list. Each case contains a stable ID, variation class, typed input model, expected outcome, expected owner, expected changed paths, and preservation requirements.

Required cases are `baseline`, `trivia`, `line-shift`, `reorder`, `file-move`, `module-move`, `unrelated-extension`, `equal-text-decoy`, `old-path-decoy`, `ambiguity`, `semantic-drift`, `already-applied`, `replay`, and `irrelevant-version`.

Generated models are inputs to a real transformation harness. They do not contain full source snapshots and do not establish behavior until typed assertions execute against the product implementation.
