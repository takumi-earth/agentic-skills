# Script-notebook variant

## Concrete intent

Persist the user's observed copy-edit-copy workflow for scratch scripts so twenty-five different approaches can remain understandable the next day without reconstructing them from Git history.

## Approach

Provide a file-oriented helper that resolves the canonical repository, defaults notebooks beneath its scratchpad, exclusively claims an immutable directory for each script version, stores exact bytes under `artifact/`, records a digest, intent, and validated predecessors, and refuses overwrite. Keep the procedure concrete instead of generalizing prematurely to every artifact type.

## Preserved nuance

The first occurrence is persisted because recurrence cannot be known ahead of time. Speculative approaches remain useful for comparison and later convergence even when they never become official tooling.

## Relationships and uncertainty

This candidate overlaps the immutable pending variants implemented by `$review-pending-skills`, but it applies the same practice to arbitrary script experimentation. The first variant intentionally supports one file; multi-file notebooks may warrant a separate competing variant rather than broadening this one silently.

## Review questions

- Should stdout remain a human-readable path or become schema-exact JSON?
- Should a later variant support copying directories while preserving symlink and size boundaries?
