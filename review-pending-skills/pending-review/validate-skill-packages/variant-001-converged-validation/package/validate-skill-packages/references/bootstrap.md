# Resolve validator tooling

Use `python3 scripts/resolve_skills_ref.py --repo <repo> --source <repo-relative-source>` for bounded discovery. Read the repository's declared pinned layout; do not search unrelated home directories. The source must resolve inside the supplied repository. Home-relative input paths are expanded for I/O and rendered as `~/...` in output.

The resolver reports these independent observations:

- CLI availability and path;
- top-level module discovery and origin, without importing the module or claiming that import execution succeeds;
- pinned source presence and project name, version, dependencies, and build backend;
- installed distribution metadata and version;
- module-origin provenance: `matches-pinned-source`, `different-origin`, `unresolved`, or `not-installed`;
- version agreement: `matches`, `different`, or `unresolved`;
- declared Python helper executable modes and interpreter recommendations;
- an inert editable-install argument list when the source metadata is usable.

The CLI defaults to `skills-ref`, the module to `skills_ref`, and the distribution name to the pinned project's name. Use `--cli-name`, `--module-name`, or `--distribution-name` for explicitly selected alternatives. Module lookup accepts a top-level identifier so it does not import a parent package as a lookup side effect.

CLI presence, discoverable module origin, and matching distribution version are distinct evidence. Metadata agreement does not establish runtime import success. Discovery reports exit `0` even when components are missing; inspect their typed states. Invalid scope or malformed input returns a nonzero diagnostic.

If installation is needed, report the pinned source, exact command and environment, dependency effects, and subsequent provenance and validator checks. Execute only with explicit environment-mutation authority. Do not mutate the pinned source to make validation pass. After an authorized install, inspect imported-module behavior through an explicitly authorized probe when runtime importability needs proof, and run the required canonical and harness gates separately.
