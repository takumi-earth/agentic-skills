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

Validate nested objects, nonempty identity fields, and normalized repository-relative paths before generation. Both original and moved paths must lie beneath the declared scope. File and module moves must each change identity. Pre-state, post-state, and drift are nonempty JSON objects and must be distinct; these checks establish model consistency, not semantic truth of the supplied states. Unrelated node IDs must be unique and distinct from the target; unrelated owners differ from the target owner. Generated owner and node IDs are allocated without colliding with supplied identities.

`trivia`, `line-shift`, and `reorder` are planning annotations with `adapter_materialization_required: true`. A consuming adapter must materialize and check each actual variation. Equal text does not merge fixture roles. Fourteen records do not establish fourteen executed behaviors.
