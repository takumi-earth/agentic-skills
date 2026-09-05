# Target output contract

The topology validator executes the target's real package-relative entry point with an environment-selected interpreter. The target must emit exactly one JSON object to stdout and keep stderr empty on success.

The JSON object must include:

- `runtime_root`: the canonical harness-state root observed by the target, as an absolute or `~/...` path;
- `repository_root`: the canonical repository root observed by the target, using either spelling;
- `side_effects`: an array of absolute or `~/...` paths created beneath `TASK_OUTPUT_ROOT`. Use `[]` for a read-only target. Declare files, symlinks, and empty directories; a declared directory covers its subtree, and parent directories of declared artifacts are implicit. Symlink targets must also remain inside the task-output root.

The object may include package-resource values, sibling-resource values, state reads, and other deterministic fields. The reserved top-level `topology` field is excluded from comparison; every nested field, including one named `topology`, remains meaningful. The validator normalizes whole package and task-output path values and descendants, never arbitrary substrings in prose or merely shared path prefixes.

The validator compares actual output artifact bytes, kinds, permissions, and link targets separately from JSON results. Undeclared output entries and observed fixture changes outside the current task-output root fail validation. An exit failure, stderr content, malformed JSON, authority mismatch, missing or escaping declared artifact, protected-state mutation, unequal result, or unequal artifact state fails the matrix.

Reports render home paths as `~/...` after internal comparisons. They identify later topology rows left unexecuted after an observed mutation, and state that arbitrary external writes and changes reverted between observations are not observed. Fixture cleanup does not undo target mutations to supplied repository or runtime state.
