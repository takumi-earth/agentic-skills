# Goal-authority regression

The regression provenance is rollout `019fe6b3-593d-74c0-89b5-9f4f8b3441fb`, raw session `~/.codex/sessions/2026/08/09/rollout-2026-08-09T21-25-41-019fe6b3-593d-74c0-89b5-9f4f8b3441fb.jsonl`. Its reproducible tool-call audit lives under `~/agentic-skills/.scratchpad/template-rs-goal-regression-2026-08-10/goal-edits/`.

The causal violation was not merely selection of the wrong Git revision. Assistant-authored mutable status was allowed to flow backward into architecture and test authority:

1. Goal edits at ordinals `827` and `3380` promoted an assistant-derived design into “decision-complete” and then partially implemented fact.
2. A parity edit at ordinal `4136` used `HEAD` rather than the user-selected `HEAD^` baseline and mixed replacement with retirement for tests of a removed remote-history capability.
3. The goal edit at ordinal `4150` recorded those dispositions as valid status and made an invented exact-selector test an obligation.
4. The source edit at ordinal `4170` implemented that invented obligation, so the assistant-authored goal edit appeared to authorize its own downstream source change.
5. The user corrected the baseline at ordinal `4244`; goal edit `4266` updated only one paragraph and left the conflicting status alive. Goal edit `4453` later performed the required whole-goal retraction.

The valid contrast is user message ordinal `4736`, which explicitly selected recovery revision `370a5039f342b088ea278e6d6df8cf0b20b37e96` before goal edit `4758` updated the complete affected recovery packets. A goal edit may record that authority because it already came from the user.

Therefore, mutable status is a sink for primary authority and current evidence, never a source. Baseline corrections invalidate dependent statements and effects until a whole-goal provenance and contradiction audit closes. Removed-capability retirement must not be converted into replacement behavior simply to make parity bookkeeping appear complete.
