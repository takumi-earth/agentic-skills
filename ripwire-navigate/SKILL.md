---
name: ripwire-navigate
description: >
  You can NAME the symbol: who calls it, what it calls, the path from A to B, its full body, or an
  exact literal/regex match. 'Safe to change or rename X — what breaks downstream?' = the transitive
  blast radius, not 1-hop callers. Three or more symbols → --connect. A one verb query stops; safety needs both.
allowed-tools: Bash, Read
---

> Modified canonical port: compact instructions and conditional references are maintained in `~/agentic-skills`; upstream skill-definition enhancements use `$manage-ripwire-skills`.
# Navigate with ripwire

Answer the named question with the smallest sufficient query. Do not start cold orientation, load every neighboring skill, or reread this unchanged body for each symbol in retained context.

| Question | Query |
| --- | --- |
| Direct callers or callees | `--callers=SYM` or `--callees=SYM` |
| Safe to change/delete a symbol | `--impact=SYM` **and** `--uses=SYM` |
| Full body and callee signatures | `--expand=SYM` |
| Exact literal or regex | `--grep=STR` or `--regex=PAT` |
| File and line instead of a name | `--at=FILE:LINE`; use the resolved `@FILE:LINE` seed |
| How A reaches B | `--path=A,B` |
| Three or more symbols, or a shared-caller connection | `--connect=A,B,C` |
| One closed code claim | `--verify='calls(A,B)'`, `uses`, `unused`, `contains`, `defines`, or `reaches` |

Run as `ripwire <dir> <query>`. For split checkouts, pass every authorized root so cross-root edges are present. `--callers` is one hop and cannot establish transitive safety; `--impact` supplies depth and `--uses` supplies non-call reference breadth.

Keep the legend on the first query that needs its schema; use `--legend=compact` on later navigation queries once that legend is known. The MCP descriptions already carry the schema. Stop once the question is answered; a new symbol reuses the same instruction contract.

High `amb=` means guessed edges. Confirm the relevant call site or use a compiler-backed SCIP overlay before relying on it. Counts marked as floors cannot prove absence. Verification may be `confirmed`, `refuted`, or `not-established`; incomplete evidence is not a negative verdict.

For variable slicing/data flow, multiple-term or structural retrieval, ambiguity/SCIP details, byte layout, deeper contract/docs investigation, or query-ranking distinctions, load [navigation-reference.md](navigation-reference.md) at that condition. It retains the exact limits and modes; do not preload it for a basic caller or literal query.

A served symbol body does not satisfy a user-required complete owner-file read or a harness's native-read prerequisite. Honor those constraints. Invocation does not grant source writes or a verification gate. An unknown symbol belongs to `ripwire-find-bug` or `ripwire-orient`; merge readiness belongs to `ripwire-change-check`.
