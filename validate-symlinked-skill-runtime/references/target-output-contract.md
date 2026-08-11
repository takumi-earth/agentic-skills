# Target output contract

The topology validator executes the target's real package-relative entry point with an environment-selected interpreter. The target must emit exactly one JSON object to stdout and keep stderr empty on success.

The JSON object must include:

- `runtime_root`: the canonical harness-state root observed by the target;
- `repository_root`: the canonical repository root observed by the target;
- `side_effects`: a nonempty array of paths created beneath `TASK_OUTPUT_ROOT`.

The object may include package-resource values, sibling-resource values, state reads, and other deterministic fields. It may include `package_root`, task-output paths, and `topology`; the validator normalizes only those topology-specific values before comparison.

An exit failure, stderr content, malformed JSON, authority mismatch, missing or escaping side effect, canonical-state mutation, runtime-state mutation, or unequal normalized output fails the topology row.
