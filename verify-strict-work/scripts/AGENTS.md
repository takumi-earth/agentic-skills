# Behavioral evaluation tooling

- This directory owns `Bun` evaluation tooling, not a product backend. Use actual `Codex` CLI events and observed fixture effects for behavioral claims. Unit tests of the evaluator establish only evaluator behavior.
- Keep all evaluation workspaces and traces under the canonical repository's ignored `.scratchpad/`. Use synthetic data and fake effect markers. Do not contact home hardware or third-party services to test a refusal.
- Preserve the user's model configuration, native approval, hook trust, and unrelated handlers. Do not bypass approval or trust. A guard success abstains rather than granting tool permission.
- Decode foreign events before grading. Return concrete structured failures; contain foreign exceptions at their immediate boundary. Never turn an absent trace or unavailable evaluation into a pass.
- Every case must grade a real effect or an independently observed invariant. Final model assurances, instruction wording, and synthetic traces cannot close agent behavior.
