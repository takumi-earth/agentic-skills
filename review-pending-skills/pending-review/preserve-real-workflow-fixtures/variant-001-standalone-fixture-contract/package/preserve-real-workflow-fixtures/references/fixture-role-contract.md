# Fixture Role Contract

## Role matrix

| Production boundary | Required fixture form | Invalid substitute | Preferred oracle |
|---|---|---|---|
| Current repository target | Dedicated committed target file or tree | Reused snapshot or runtime-built document | Parsed final state plus workflow outcomes |
| Materialized template snapshot | Dedicated committed snapshot input | Current-target fixture reused for convenience | Typed plan and lifecycle observations |
| Manifest, sidecar, or policy file | Committed file loaded exactly | `.replace()`, `format!`, marker substitution | Parsed semantic model unless bytes are contractual |
| Valid Rust source | Committed `.rs` file | Inline valid program string | Compiler, parser, or workflow result |
| Invalid non-compiler snippet | Fenced code in inert text or Markdown | Checked-in `.rs` accidentally linted as valid source | Parser rejection or diagnostic value |
| Compile-fail integration case | Committed source only when `rustc` behavior is the contract | Incidental malformed source | Typed compile result and diagnostic fixture |
| Pure string parser input | Inline string may be valid | Unnecessary fixture file | Typed parse result |

## Decision sequence

1. Remove test-helper names and ask what production consumes.
2. Name the artifact role before choosing a pathname or constant.
3. Decide whether path, extension, filesystem layout, external tooling, or exact bytes affect behavior.
4. If any do, create a role-specific committed fixture and load it without modification.
5. If none do and the API truly accepts only a value, keep the input inline.
6. Choose a semantic oracle independently from the input construction.

## Counterexamples

- Two byte-identical TOML files can be correct when one is a current target and one is a materialized snapshot. Their independent filenames pin the handoff being exercised.
- A rendered snapshot derived from the same inline document does not prove a workflow consumed a real snapshot.
- A short valid Rust function remains source and belongs in a `.rs` fixture when the workflow consumes source files.
- An invalid syntax example used only as parser data should not become a compiled `.rs` file.

