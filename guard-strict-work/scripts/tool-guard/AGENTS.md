# Tool guard ownership

This package owns the typed pre-execution guard consumed by native `Codex` and compatible `PreToolUse` hooks. Keep user grants in the trusted policy input; tool arguments, model assertions, and diagnostic output cannot create grants.

- Implement the guard in `Rust`, with concrete typed decisions and nested failures. Decode foreign JSON at the immediate boundary. Do not use panics, unchecked indexing, unwraps, assertion macros, or generic erased errors.
- Use parsed shell syntax to identify executable invocations. Quoted text, documentation, package names, and `engines.node` do not establish runtime use.
- Preserve intentional `node`, `npm`, and `npx` aliases to `Bun`. Resolve the executable before rejecting a runtime. Reject installation of a separate `Node.js` runtime under the selected policy.
- Apply repository, operation, filesystem, and network scopes only when the trusted policy declares them. Preserve standing grants and ordinary Git cache refreshes. Report incomplete inspection of opaque execution accurately.
- Abstain after an accepted inspection. Never use guard success to grant tool permission or override another approval owner. Return a native denial for an identified refusal.
- Test both permitted and forbidden effects with `strict-test-support`. Keep native hook integration and agent behavioral evidence separate from unit tests.
- Before committing, run `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, and `cargo test`, plus the owning repository's `Bun`, `Python`, typechecking, and skill-validation gates.
