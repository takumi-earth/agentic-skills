# Configuration Reference

Load this reference when `agentic-skills.toml` exists or the user wants persistent harness selection, custom paths, allowlists, exclusions, or automatic handling of newly added skills.

## Lookup and authority

The CLI uses the first applicable config in this order:

1. The explicit `--config` path.
2. `${XDG_CONFIG_HOME:-~/.config}/agentic-skills.toml`.
3. `~/agentic-skills.toml` as a compatibility fallback.

If both automatic paths exist, the XDG path wins and the CLI warns about the ignored fallback. `sync --config` requires that explicit file to exist. `init-config --config` uses that path only when no file exists there.

The presence of any selected config disables all default routing. Only `[harness.<name>]` sections in the file are processed; omitted harnesses and any existing links in their directories are untouched.

## Schema

Use schema version `1`. Every harness requires `mode`, `new_skills`, and `skills`. `exclude_skills` is optional and defaults to an empty list.

```toml
schema_version = 1

[harness.agents]
mode = "always"
new_skills = "link"
skills = ["link-agentic-skills"]
exclude_skills = []

[harness.workbench]
mode = "detected"
detect_dir = "~/.workbench"
skills_dir = "~/.workbench/skills"
new_skills = "ignore"
skills = ["link-agentic-skills"]
exclude_skills = []
```

Harness names and skill names must use lowercase hyphen-case. Unknown keys are rejected. Configured paths must be absolute or start with `~/`; the CLI expands `~` against the selected `--home`. A destination may not be a filesystem root, the selected home itself, or any path that contains or is contained by the selected source root.

Built-in harness sections may omit `detect_dir` and `skills_dir` to use their registered paths. A custom harness requires `skills_dir`. Custom `mode = "detected"` also requires `detect_dir`.

## Routing fields

`mode` controls whether a missing destination is eligible:

- `"always"` creates `skills_dir` even when no harness root is present.
- `"detected"` uses an existing `skills_dir` or requires the configured detection directory. If the detection directory exists, a missing `skills_dir` is created. If neither exists, the harness is skipped with exit `0`.

`new_skills` controls source packages not already listed:

- `"link"` adds every current, nonexcluded source skill to `skills`, even while the harness itself is absent.
- `"ignore"` leaves unlisted source skills out, making `skills` an explicit allowlist.

`exclude_skills` always wins over `skills` and `new_skills`. During sync, names no longer present in the source repository are removed from both arrays. A newly excluded, deselected, or removed package causes link removal only when the existing entry is an owned relative link to this repository.

Before mutation, the CLI validates every route and materializes the complete link plan. When routing arrays change, it atomically rewrites the entire supported document in canonical order before applying harness changes. It preserves an existing file's permission mode and follows a valid config-file symlink, but comments and custom ordering are lost. If the config write fails, no harness changes begin. If routing is already current, the original file is left byte-for-byte unchanged. Use `sync --dry-run` to review `config.changes` and `config.write_status` before a rewrite.

## Built-in registry

| Harness | Detection directory | Skills directory | Default mode |
| --- | --- | --- | --- |
| `agents` | none | `~/.agents/skills` | `always` |
| `codex` | `~/.codex` | `~/.codex/skills` | `detected` |
| `claude` | `~/.claude` | `~/.claude/skills` | `detected` |
| `gemini` | `~/.gemini` | `~/.gemini/skills` | `detected` |
| `kiro` | `~/.kiro` | `~/.kiro/skills` | `detected` |
| `copilot` | `~/.copilot` | `~/.copilot/skills` | `detected` |
| `cursor` | `~/.cursor` | `~/.cursor/skills` | `detected` |
| `cline` | `~/.cline` | `~/.cline/skills` | `detected` |
| `windsurf` | `~/.codeium/windsurf` | `~/.codeium/windsurf/skills` | `detected` |
| `opencode` | `${XDG_CONFIG_HOME:-~/.config}/opencode` | `${XDG_CONFIG_HOME:-~/.config}/opencode/skills` | `detected` |

`init-config` writes `agents` and those built-ins currently detected, selects all current source skills, uses `new_skills = "link"`, and begins with no exclusions. It refuses to overwrite either selected automatic config or an existing explicit path. With `--dry-run`, its JSON report contains the complete proposed TOML without writing it.

## Multiple repositories

Run the CLI separately from each canonical repository, passing `--skills-root` explicitly when needed. A repository owns only relative links targeting its same-named packages. If two repositories offer the same skill name to one harness directory, the second run reports the first repository's link as a conflict and preserves it. Resolve that namespace choice in config; never make a harness skill root point at an entire repository.
