# Review-surface audit rules

The auditor reports advisory findings for these phrase relationships:

- `review`, `audit`, `diagnose`, or `inspect` near unconditional `write`, `save`, `persist`, `create a report`, or `.scratchpad` language;
- review triggers near unconditional helper, collector, probe, test, build, or validation commands;
- diagnosis near `fix`, `rewrite`, `apply`, `stage`, `commit`, or `push` without a separate-authority clause;
- creation or promotion near `install`, `link`, `sync`, `register`, `enable`, `hook`, `publish`, or `deploy` as one combined effect;
- broad words such as `automatically` or `always` spanning multiple effect classes without explicit trigger ownership.

The auditor reduces severity when nearby text explicitly says `only when requested`, `separate authority`, `does not authorize`, `do not`, or equivalent. It does not attempt full natural-language authority proof.

Each finding includes file, line, rule ID, effect classes, excerpt, and advisory severity. Review the complete surrounding section before changing a skill.
