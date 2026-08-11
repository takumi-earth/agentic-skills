# Rendered-source oracle flow model

The bundled analyzer uses a deliberately small, explicit flow model over Python-like test code. It is a reusable prototype, not a compiler-integrated proof.

## Producers

Calls whose results derive from structural source:

- `render_source`, `rendered_source`, `to_source`;
- `syntax_text`, `node_text`, `transformation_output`.

## Propagators

Assignments, simple aliases, and configured wrapper calls propagate taint. A call to `parse_source` does not clear taint; converting a parsed node back through `syntax_text` is still rendered-source provenance.

## Oracle sinks

Flag tainted values reaching:

- membership tests and `contains` wrappers;
- `startswith`, `endswith`, regex search or match;
- raw equality or inequality;
- snapshot helpers;
- occurrence counts used in assertions.

## Exact-output exemptions

Functions decorated with `@exact_output_contract` are exempt only within that function. The exemption asserts suite ownership; it must not be inferred from a filename or string method.

## Limits

The prototype handles direct assignments and calls in one file. Dynamic dispatch, imports, reflection, aliasing through containers, and macros require a language-aware implementation. `unknown` flow should remain visible during review rather than being treated as safe.
