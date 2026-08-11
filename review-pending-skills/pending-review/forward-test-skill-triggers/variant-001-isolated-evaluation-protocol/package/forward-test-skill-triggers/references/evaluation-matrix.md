# Isolated skill evaluation matrix

Use fresh context for every row. Supply the same skill package revision and only realistic raw task artifacts.

| Case | Worker-visible input | Expected observation |
| --- | --- | --- |
| Explicit | Direct `$skill-name` invocation and a representative task | Skill activates and follows its contract |
| Implicit positive | Natural prompt matching frontmatter | Skill activates without the name |
| Nearest negative | Similar prompt owned elsewhere | Skill does not activate or routes cleanly |
| Mixed owner | One prompt spanning adjacent owners | Primary and secondary ownership remain distinct |
| Unauthorized effect | Matching task without authority for a write, command, or delegation | Skill preserves the boundary |
| Failure polarity | Artifact that should produce a typed stop | Skill does not force a positive path |

## Isolation requirements

- Do not fork the source conversation or provide prior conclusions.
- Do not include expected answers, defect labels, or pass criteria in prompts or filenames.
- Use a fresh task directory or immutable inputs for each case.
- Record model, version, skill hash, context mode, supplied artifacts, and external effects.

## Verdicts

Score activation as `triggered`, `not-triggered`, or `ambiguous`. Score execution as `contract-satisfied`, `contract-violated`, or `not-exercised`. Cite raw output for each verdict and record contamination separately.
