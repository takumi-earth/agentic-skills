# Fixture Role Contract

## Role matrix

| Scenario contract | Fixture form | Invalid substitute | Preferred oracle |
|---|---|---|---|
| Distinct current target and snapshot identities | Separate materialized roles; dedicated committed files when explicitly required | Reusing one identity when the workflow must distinguish two | Parsed final state plus workflow outcomes |
| Exact starting manifest, sidecar, or policy bytes | Load the specified artifact unchanged | Substitution or rendering that changes the required starting state | Parsed model plus any contractual byte assertion |
| Filesystem layout or toolchain behavior | Materialized files with the required paths and extensions, including controlled temporary workspaces | Invoking only a value-level helper and claiming the file boundary ran | Workflow, compiler, or generator outcome |
| Valid parser input or structural model | Small strings, tokens, IR, or files according to the public input contract | Treating a parser call as evidence of compiler or workflow execution | Typed parse or structural result |
| Invalid non-compiler snippet | Inline data or inert text fixture | Source accidentally included in unrelated compiler/linter discovery | Parser rejection or diagnostic value |
| Compile-fail integration case | Source arranged for the compiler harness, committed when required | Incidental malformed parser data presented as compiler evidence | Typed compile result and diagnostic fixture |
| Pure string parser input | Inline string may be valid | Unnecessary fixture file | Typed parse result |

## Decision sequence

1. Remove test-helper names and ask what production consumes.
2. Name the artifact role before choosing a pathname or constant.
3. Decide whether path, extension, filesystem layout, external tooling, or exact bytes affect behavior.
4. Preserve the required identities and starting state. Use dedicated committed files and exact loading when the scenario explicitly requires them.
5. Otherwise choose the smallest faithful setup, including inline values, controlled mutations, or temporary files. File consumption does not by itself decide how the starting files are constructed.
6. Choose a semantic oracle independently from the input construction.

## Counterexamples

- Two byte-identical TOML files can be correct when one is a current target and one is a materialized snapshot. Their independent filenames pin the handoff being exercised.
- A rendered snapshot derived from the same inline document does not prove a workflow consumed a real snapshot.
- A short valid Rust function may be parser data in memory or a materialized `.rs` file for a toolchain scenario; its required boundary decides which.
- An invalid syntax example used only as parser data should not become a compiled `.rs` file.
