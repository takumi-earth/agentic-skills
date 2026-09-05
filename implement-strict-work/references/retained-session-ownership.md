# Retained Session Ownership

Load this reference when replacing an execution backend while preserving the selected session or cell owner. It does not freeze an old owner during an explicitly requested session-management redesign or apply to a routine backend bug fix.

## Preserve the responsibility boundary

Identify the affected owners of admission, cell identity, task registration, callbacks, observation, shared-state commits, completion, and shutdown. Distinguish those responsibilities from execution, transport, process provisioning where applicable, and runtime termination.

Keep the execution path consistent with the selected ownership:

```text
host -> retained session/cell owner -> low-level runtime adaptation -> execution backend
```

This chain describes responsibilities; it does not require a new wrapper or public adapter abstraction. Existing adaptation may translate requests, replies, handles, and lifecycle evidence at the appropriate boundary.

Prohibit a second owner of session admission, cell registration, shared-state policy, callback supervision, or session completion. Permit subordinate request-correlation maps, process-handle tables, and runtime resource bookkeeping that do not acquire those authorities. A convenient public or tested high-level runtime service does not justify nesting another session algorithm beneath the retained owner.

## Keep lifecycle behavior observable

- Preserve admission and shutdown ordering so an accepted cell cannot escape task registration and the shutdown wait.
- Preserve callback cancellation and drainage before the terminal cleanup or delivery that depends on them.
- Preserve shared-state commit and cancellation arbitration. An input snapshot cannot replace concurrently owned state. Transfer the required writes when the boundary needs that representation; preserve direct shared-state access when that is the selected contract rather than imposing a new write-set protocol.
- Distinguish a guest result from the runtime termination or quiescence evidence required by completion, interruption, and shutdown. For process backends, preserve actual process exit and child reaping; for an in-process backend, observe its real termination boundary without inventing a child-process protocol.
- Preserve the host's real pending-frontier behavior when required. A timed yield or a similarly shaped return value is not equivalent evidence.

Use session-owner tests for admission, callbacks, shared state, and completion; use runtime-owner tests for the applicable execution and protocol behavior. A test of duplicated machinery may identify a live contract without making that machinery the production owner. Map touched tests to the retained behavior instead of retiring it with the old engine-specific implementation.

## Converge the selected replacement

When the replacement is exclusive, remove the old backend's source, initialization, handles, backend-specific dependency declarations, and build wiring within the approved scope. A disabled feature or fallback path does not satisfy selected removal. Converge lockfiles through the authorized dependency workflow and retain dependency nodes still required by surviving consumers.

Do not expand into excluded build systems or historical surfaces merely to make a textual search empty. Engine-neutral session responsibilities do not authorize an interchangeable-backend or plugin framework.

Apply an already-selected retained-owner design without renewed approval or an audit packet. When the user says that design was always intended, treat conflicting duplication as remediation. Use `$protect-causal-architecture` only for a still-unresolved owner or ordering choice; this reference grants no additional mutation, verification, persistence, or delegation authority.
