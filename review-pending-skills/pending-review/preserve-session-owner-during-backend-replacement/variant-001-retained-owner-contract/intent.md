# Retained session owner during backend replacement

## Origin and intent

The user corrected the `codex-bun` architecture on 2026-09-05: preserving `codex-code-mode-runtime` and adapting it directly to Bun's low-level runtime was always the intention. The user explicitly rejected stacking `CodeModeService` below the parent session owner and retaining any V8 backend. The subsequent approval was: "Yes, that's all spot on. And, I'm ok for you to be creating additional reusable skills that reinforce this as well."

This variant makes backend replacement a distinct trigger. It retains the concrete admission/shutdown, callback, shared-write, process-exit, and pending-frontier distinctions that a generic ownership reminder can miss. It does not make Bun or Cargo a universal runtime choice.

## Relationship and risk

`$protect-causal-architecture` owns genuinely disputed causal decisions; this candidate applies the already-selected session owner during implementation. `$guard-strict-work` supplies authority and scope constraints. The main risk is invoking the skill for an intentional session redesign; the trigger excludes that request and the body preserves explicit user choices.

## Written review scenarios

- Positive: replace an embedded engine with a child-process engine while preserving the host session API. Expect a narrow low-level adapter and retained admission, callbacks, and completion ownership.
- Regression: the replacement runtime exposes a convenient session service. Expect rejection of nested registries and shared-state owners, even if that service has existing tests.
- Regression: a guest sends its result before its process exits. Expect the shutdown barrier to wait for genuine runtime-exit evidence.
- Negative: the user explicitly requests redesigning session management. This candidate must not turn the old owner into a permanent prohibition.

These are written scenarios, not executed behavioral or independent-agent evidence.

## Artifact and activation boundary

The nested package is pending review. Creation does not promote it, install or synchronize it, register a hook, or authorize a backend migration. No executable resources are included.
