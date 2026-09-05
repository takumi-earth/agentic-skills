# Review-surface audit rules

The auditor reports advisory findings for these phrase relationships within a review-oriented entrypoint or direct Markdown reference:

- `review`, `audit`, `diagnose`, or `inspect` context with unconditional `write`, `save`, `persist`, `create a report`, or `.scratchpad` language;
- review context with unconditional helper, collector, probe, test, build, or validation commands;
- diagnosis near `fix`, `rewrite`, `apply`, `stage`, `commit`, or `push` without a separate-authority clause;
- creation or promotion near `install`, `link`, `sync`, `register`, `enable`, `hook`, `publish`, or `deploy` as one combined effect;
- broad words such as `automatically` or `always` spanning multiple effect classes without explicit trigger ownership.

The entrypoint establishes review or creation context for its direct references; blank lines do not erase that context. Creation-to-activation findings do not require a review keyword. Boundary matching stays within a statement: a negated action or a conditional user request matching that effect can suppress a lead. A request to review does not grant report creation, and a neighboring prohibition does not suppress unrelated actions. Git and activation verbs are matched separately, so permission to commit cannot suppress a push lead.

These are lexical heuristics, not verified authority. Quoted examples can still match, and unfamiliar wording can escape the declared patterns. Every emitted finding remains advisory; a zero-finding result establishes only that no unsuppressed declared pattern matched.

Resolve the package and each input before reading bytes. Accept the selected package through a symlink, require every entry or reference target to remain inside that resolved package, and read each resolved file once. Deduplicate self-references and aliases. Scan simple inline local Markdown links with optional fragments; skip external URLs and do not follow indirect reference chains. Compute the reported hash and findings from the same bytes.

Return one JSON report with process status `0` for no findings, `1` for advisory findings, or `2` for input errors. Preserve the report envelope on missing, invalid, or escaping inputs. Render home paths as `~/...`, including excerpts and errors. The script creates no evidence files or other output artifacts.

Each finding includes file, line, rule ID, effect classes, excerpt, and advisory severity. Review the complete surrounding section before changing a skill.
