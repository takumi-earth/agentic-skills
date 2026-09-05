---
name: preserve-session-owner-during-backend-replacement
description: "Replace an execution backend beneath an existing session or cell owner without duplicating its lifecycle machinery. Use when a migration retains host session behavior but swaps the runtime mechanism; not for an explicitly requested session-management redesign or routine backend bug fix."
---

# Preserve Session Ownership During Backend Replacement

A replacement engine does not become the owner of the surrounding session algorithm. Preserve the user-selected owner and connect its existing machinery to the new low-level execution capability.

## Keep the boundary explicit

Read the selected architecture and the directly affected host/runtime boundary. Identify who owns admission, cell identity, task registration, callbacks, observation, shared-state commits, completion, and shutdown. Distinguish those responsibilities from process provisioning, guest execution, transport, and termination.

When the user retains the session owner, keep the execution path narrow:

```text
host → retained session/cell owner → integration adapter → low-level runtime → engine
```

The adapter translates requests, replies, handles, and lifecycle evidence. It must not introduce a second registry, shared store, callback supervisor, or completion authority. Do not wrap a high-level service inside the retained session manager merely because that service is already public or tested.

## Preserve behavior at its actual owner

- Preserve admission/shutdown ordering: an accepted cell cannot escape the task-tracking wait.
- Preserve callback cancellation and drainage before the terminal cleanup or delivery that depends on them.
- Preserve shared-state commit and cancellation arbitration. An input snapshot is not an authoritative replacement for concurrent shared state; transfer the required write set through the adapter.
- Distinguish a guest result from process exit. Keep shutdown, interruption of a busy guest, and child reaping observable through the low-level boundary.
- Preserve real pending-frontier behavior when the host requires it. Timed yielding or a similarly shaped return value is not equivalent evidence.

Use owner-level tests for session behavior and runtime-level tests for process/protocol behavior. A test of duplicated machinery can identify a still-live contract without selecting that machinery as the production owner. Do not retire a behavior merely because its old engine-specific test is removed.

## Replace the selected backend completely

Follow the user's removal scope. If the replacement is exclusive, remove the old backend's source, initialization, handles, dependencies, lock entries, and build wiring within that scope; a disabled feature or fallback implementation is not removal. Do not introduce a plugin framework from the phrase "engine-neutral."

Do not expand into excluded build systems or enclosing directories to make a textual search empty. Runtime removal and repository-wide historical erasure are different requests.

## Handle drift without reopening intent

When the user says the retained-owner design was always intended, treat existing duplication and protocol leaks as remediation, not newly discovered cons that require choosing the architecture again. Ask only if the actual integration forces a still-unresolved owner or behavior decision. This skill supplies no additional mutation, verification, or delegation authority.
