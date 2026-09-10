# Profile compatibility and fallback

This reference completes the proposed event-root consumer. It does not install a producer, change hook configuration, or authorize a new runtime invocation.

| Observation in managed-reference mode | Result |
| --- | --- |
| Bound version 1 context, custom root, different inherited `CODEX_HOME` | Use the event root and report the conflict. |
| Bound version 1 context with equal or absent environment root | Use the event root. |
| Version 1 was selected but the field is missing | `missing-runtime-context`; no fallback. |
| Present `null`, wrong type, empty/relative root, duplicate key, or unknown field | `invalid-runtime-context`; no fallback. |
| Unknown version or pathname grammar | `unsupported-runtime-context`; no fallback. |
| Untrusted channel or foreign/unmapped namespace/home | `unbound-runtime-context`; no local-home expansion. |
| Declared legacy profile and context omitted; `CODEX_HOME` present and usable | Use the inherited root, labeled `CODEX_HOME`. |
| Declared legacy profile and context omitted; `CODEX_HOME` present but empty, relative, missing, or unusable | Preserve `invalid-runtime-root`; do not fall back. |
| Declared legacy profile and both context and `CODEX_HOME` omitted | Use `~/.codex` only in the established local-home context; validate it normally. |
| Neither a supported profile nor a trusted fallback-home context | Report unavailable authority; no package-location or attachment enumeration fallback. |

In exact-user-path mode, a path supplied independently by the user's current designation uses its own established namespace/home/base. That mode is not a recovery strategy for malformed managed metadata. A relative path without a base returns the shared `invalid-goal-base` outcome. A missing or non-regular final file returns `artifact-not-file`; it does not authorize searching for another file or recreating the selected one.

The producer's version 1 profile supports a trusted local launcher only. Use the declared `posix` or `windows` grammar before joining or comparing paths; do not reinterpret a Windows drive, UNC path, or backslash with POSIX path rules. A consumer without the matching implementation reports unsupported context. Home normalization must preserve component boundaries and the bound producer home. Copied events are evidence, not authority to access similarly spelled local paths.

Negotiate the profile before delivery to strict consumers. Old handlers that reject extra fields retain the legacy event shape; a new handler requires the selected new shape. The inspected Codex dispatcher serializes one input before matched-handler execution, so mixed profiles require a producer change. This specification does not claim that merely adding a field preserves old handlers.

On resume or a supported fork, derive root authority from the runtime actually executing the new event. Do not cache a previous process's root as a durable goal association. Preserve the goal's explicit selection separately; root changes can make its file unavailable without reopening the user decision.

Evaluate the table against custom/default roots, missing and malformed fields, conflicting environments, strict old consumers, copied events, explicit external and relative filenames, missing files, and supported resume/fork contexts. These are specification cases. Runtime/root checks and hook execution remain unrun until a selected implementation is authorized. Use the existing response or authorized record for results; no new audit artifact, stderr stream, or persistence gate follows from classification.
