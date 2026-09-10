# Rendered-source oracle flow model

The scanner analyzes explicitly selected Python files. Its result is advisory; it does not parse Rust or prove product behavior.

## Supported provenance

`render_source`, `rendered_source`, `to_source`, `syntax_text`, `node_text`, and `transformation_output` produce rendered text. `parse_source` and `ast.parse` produce structural values. Converting those values through a text producer restores text provenance.

Straight-line assignments replace prior provenance. Direct local functions bind positional and keyword arguments and propagate return values, including helper-produced source; their assertion bodies are evaluated with the supplied values. `--wrapper NAME` explicitly declares a value-preserving wrapper. Text formatting methods preserve text provenance. Dynamic calls and unsupported expressions carry unknown coverage instead of being treated as clean.

On a structural receiver, the declared query model recognizes `functions`, `owners`, `nodes`, `query`, `find`, and `function_count`. Structural cardinality through `len` is not rendered-source equality. These names describe the supported model, not verified runtime types or arbitrary methods with similar names.

## Assertion boundaries

Text-derived membership, equality, prefix/suffix, occurrence counts, regex, and substring checks are findings when consumed by an assertion. Snapshot helpers and named equality assertion helpers are sinks themselves. Local assertion helpers are inspected through their bodies. A text query used only for non-assertion preparation is not itself an oracle finding.

`@exact_output_contract` exempts only the decorated function's own assertions. It does not exempt nested or called functions. The annotation is a caller declaration of an exact-output contract, not proof that such ownership is legitimate.

## Coverage and errors

Unmodeled calls, dynamic dispatch, container aliasing, destructuring, recursion, variadic arguments, and control flow are disclosed as unknown. Uncalled module functions are also disclosed; this is not a whole-program or reachability proof. Parameters without supplied values remain unknown; default-expression semantics and mutable closure effects are not modeled. Input errors remain structured, paths use `~/...`, and hashes identify original file bytes.

Exit `0` is clean within this model; `1` reports findings; `2` reports input errors; `3` reports unknown coverage without findings. Findings and unknown coverage can coexist. No result authorizes source changes, CI adoption, or another evidence artifact.
