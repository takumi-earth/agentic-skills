# Resolver states

The resolver emits these independent components:

- `cli`: `present`, `missing`, or `error`, with discovered path.
- `module`: `present`, `missing`, or `error`, with import origin and version when available.
- `source`: `present`, `missing`, or `invalid`, bounded to the supplied repository-relative path.
- `metadata`: declared project name, version, dependencies, and build backend when parseable.
- `provenance`: `matches-pinned-source`, `different-origin`, `unresolved`, or `not-installed`.
- `helpers`: `.py` files under declared script locations with executable-bit and interpreter recommendations.
- `install_plan`: inert argument list for an editable install of the exact source.

Source presence never implies install authority. CLI presence never proves module provenance. A non-executable Python helper is usable through `python3` when Python is its declared language.

The resolver does not inspect sibling repositories, global caches, shell startup files, or arbitrary home paths.
