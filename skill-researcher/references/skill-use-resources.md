# Optional skill-use evidence resources

Use either helper independently when an authorized research question needs it. They are opt-in supplements to `extract_session_evidence.py`; they do not replace its message, goal, tool-output, or bounded-context extraction. Neither helper executes transcript commands, scans skill roots, writes reports, changes links, or synchronizes packages.

## Catalog-backed transcript leads

Use `scripts/resolve_catalog_skill_use.py` when the session's supplied catalog contains skill paths that cannot be represented by one installed root. Supply an existing catalog or prepare one only when that preparation belongs to the requested research. Do not reconstruct a historical catalog from today's installation and call it contemporaneous evidence.

```json
{"skills":[{"name":"example-skill","path":"~/skills/example-skill/SKILL.md"}]}
```

From this package:

```bash
python3 scripts/resolve_catalog_skill_use.py \
  --catalog <catalog.json> --transcript <rollout.jsonl>
```

The JSON report separates:

- `assistant_references`: exact `$name` tokens in assistant message text, with all matching catalog paths and an explicit `ambiguous` flag. A quotation or negation is still a reference, not a declaration of use. Repeated identical name/path entries are deduplicated; distinct paths sharing a name remain distinct.
- `tool_path_mentions`: exact catalog path tokens in function/custom tool inputs, with source line, tool name, skill name, and lexical path. A path inside a printing command is only a mention.
- `read_command_candidates`: recognized direct shell reads of exact catalog operands. The supported subset is `cat`, `head`, `tail`, and numeric print ranges in `sed`, supplied through native `exec_command` arguments or a plain-shell custom `exec` input. Unknown flags, wrappers, shell composition, dynamic expansion, JavaScript orchestration, and other readers remain path mentions only.

The helper streams typed Codex `response_item` JSONL records. It ignores developer/system catalog text and does not infer successful reads from submitted commands. It does not inspect tool outputs or assess faithful behavior; use the existing extractor and exact surrounding evidence for those questions. It preserves catalog-relative paths without guessing a historical working directory, accepts home-relative and expanded lexical aliases, and never resolves catalog symlinks or reads skill bodies.

## Current projection topology

Use `scripts/resolve_skill_topology.py` only when the question needs current identity or body equality for caller-selected projections. Current topology cannot establish where a historical path pointed or whether an agent used a skill.

```bash
python3 scripts/resolve_skill_topology.py \
  --projection 'installed=~/skills/example-skill' \
  --projection 'source=~/agentic-skills/example-skill/SKILL.md'
```

Each projection names a package or its `SKILL.md`. The report keeps the lexical path, canonical body path, current filesystem identity, and body SHA-256 separate. `lexical_symlinks` records links on the supplied body path, including ancestor directories; it is not an inventory of every link traversed inside link targets. Relative link targets remain relative, and home paths render as `~/...`.

`content_groups` means equal `SKILL.md` bytes only. Equal copies retain separate paths and identities; the report does not claim that scripts, references, metadata, or complete packages match. These are current observations, not an atomic snapshot across changing projections.

Both helpers emit one JSON report on stdout and exit `0` on success. Invalid inputs and filesystem failures emit a diagnostic on stderr, no partial report, and exit `2`. If a requested workflow needs persisted output, use its authorized destination; task-local generated evidence belongs under the resolved canonical repository's `.scratchpad/`.

Run the direct resource tests from this package with:

```bash
python3 scripts/test_skill_use_resources.py
```
