---
name: no-filter-heavy-output
description: A skill to setup / refine the `no-filter-heavy-output` skill for Claude Code. 
user-invocable: true
disable-model-invocation: true
---

# no_filter_heavy_output.py — Claude Code PreToolUse(Bash) gate.


## WHAT IT DOES

Denies any Bash command that pipes the output of an EXPENSIVE command into a
FILTER, and replies to the agent with the fix. Examples that BLOCK:

    cargo test 2>&1 | tail -20              bun lint | grep error
    RUSTFLAGS="..." cargo clippy | tail     gh api /repos/o/r | jq '.[]'
    psql -c 'SELECT ...' | grep alice       kubectl get pods | grep web
    cat q.sql | psql | grep result          curl -s URL | jq '.items'
    cat urls | xargs curl -s | jq .         pytest | grep FAIL | head

The rejection message tells the agent: run the command ONCE without the pipe —
the harness auto-saves the full output to a temp file — then use the Grep/Read
tools on that saved file as many times as needed.

It ALSO denies manually CAPTURING a command's output to a file (ANTI-PATTERN 2) —
`>`, `>>`, `2>`, `&>`, an explicit `1>`/`N>`, or `tee FILE` — for the same reason:
the harness already persists every command's full output to a temp file, and a
tool that owns an output file (a coverage/report command writing `cov/summary.txt`)
should write it through its own logic. Examples that BLOCK:

    git diff > /tmp/x.diff                   cargo clippy 2>&1 > /tmp/c.txt
    cargo llvm-cov report > cov/summary.txt  git diff | tee out.diff

ALLOWED here: discarding to /dev/null, fd duplications (`2>&1`, `>&2`), authoring
literal content (`echo x > f`, `cat > f <<EOF`), and feeding the captured file to
a real (non-filter) consumer in the same command (`a > /tmp/a; diff /tmp/a x`).

### WHY (the problem this solves)

Filtering an expensive command's output AT THE PIPE couples slicing to
execution. When the filter is wrong, the whole expensive command is re-run to
re-slice — recompiling, re-testing, or re-hitting a DB/API (latency, load, rate
limits; a query may even return different data each run). Prose guidance
(CLAUDE.md) and blunt permission deny-rules both failed at stopping this: prose
loses to the model's priors at generation time; broad/mute deny-rules just get
retried around. A PreToolUse hook intercepts deterministically and — the key
difference from a deny-rule — its rejection message carries the *alternative*, so
the agent redirects instead of retrying.


## DESIGN

### PIPELINE-AWARE, classifying by COMMAND WORD (never substring match).

1. SEGMENT  the command into STATEMENTS (on top-level `;  &&  ||  \n`) and each
   statement into STAGES (on top-level `|`) with `_pipelines()` — a quote / paren /
   here-doc-aware tokenizer.  A `|`/`&&`/`;`/newline is a SPLIT POINT only when it
   is STRUCTURAL: not inside '…' "…" `\``, not backslash-escaped, not within
   `$(…)`/`(…)`/`${…}`, and not inside a here-doc body.  So `grep -E "a|b" | head`,
   `cargo run -- --filter "x | y"`, and `cat <<'EOF' … a | b … EOF` are read
   correctly (the in-data `|` is not a pipe).  This is a bounded tokenizer, NOT a
   shell interpreter — it only locates structural operators (see LIMITATIONS).

2. CLASSIFY each stage by its effective COMMAND WORD.  `_command_word(stage)`
   resolves the real command by stripping, in order:
     - leading env assignments, INCLUDING quoted values:  RUSTFLAGS="--cfg a b"
     - command-runner wrappers that take another command as an argument:
       sudo / env / xargs / parallel / timeout / nice / stdbuf / ...
       (so `xargs curl -s` resolves to `curl`, `sudo -u pg psql` to `psql`,
        `timeout 300 cargo test` to `cargo`).
   The resolved word decides the stage's kind:
       _is_heavy(stage)  -> an expensive PRODUCER
       _is_filter(stage) -> a slicing/truncating CONSUMER
   Because we classify by command word, `grep 'cargo test' | head` is NOT a
   match — the producer word is `grep`; the keyword inside the argument is
   irrelevant.

3. DECIDE: block iff some FILTER stage is DOWNSTREAM of some HEAVY stage
   (filter index > first heavy index).  This covers, in one rule:
       heavy | filter                       cargo test | tail
       heavy | filter | filter              bun test | grep | head
       cheap | heavy  | filter  (mid-pipe)  cat q.sql | psql | grep
   and deliberately does NOT fire for:
       filter | heavy   (heavy is last; nothing downstream filters it)
       cheap  | heavy   (`echo sql | psql` — the query isn't being filtered)

### WHAT COUNTS AS "HEAVY" (a producer not worth re-running)

  HEAVY_BARE          bare tools that are themselves expensive: compilers, test
                      runners, type-checkers, linters, bundlers, build systems,
                      AND query/fetch tools (curl/wget; gh/glab/aws/gcloud/az/
                      kubectl/...; psql/mysql/sqlite3/duckdb/redis-cli/...).
                      Versioned/cross compilers (gcc-13, aarch64-...-gcc-13) via
                      _COMPILER; python / python3.12 via _PY.
  HEAVY_SUB           managers heavy ONLY for specific subcommands —
                      go/uv/pip/docker/deno + the bounded compilers zig/nix and the
                      firecrawl fetch CLI.  Keeps `go env | grep`,
                      `docker ps | grep`, `nix flake metadata | jq`,
                      `zig version | head`, `firecrawl --status | head` ALLOWED.
  SCRIPT_RUNNER_CHEAP INVERTED runners: heavy for ANY subcommand EXCEPT a small
                      cheap allowlist.  Covers bun/npm/yarn/pnpm (so `bun lint`,
                      `bun tsc`, `npm view`, arbitrary `bun <script>` are heavy);
                      cargo (heavy for every subcommand except the JSON/path probes
                      metadata/pkgid/locate-project/... — catches the unbounded
                      third-party `cargo-*` tail tree/update/info/search/xtask/
                      llvm-cov/machete/... while keeping `cargo metadata | jq`
                      cheap); and task-runners just/task (any recipe name is heavy;
                      bare runner and --list are cheap).
  ALWAYS_HEAVY        npx / bunx / ... (run arbitrary tools).
  Exempt             any stage containing `--version` / `--help` (cheap probe).

### WHAT COUNTS AS A "FILTER" (a consumer that slices/truncates)

  FILTER_TOOLS: grep/rg/head/tail/sed/awk/wc/cut/sort/uniq/less/column/... PLUS
  jq/yq/bat/cat/tee.  jq/cat/bat/tee are filters ONLY as a DOWNSTREAM stage; as
  the FIRST command they read a file and are cheap (`jq . file`, `cat f | rg`).
  NOT filters: `| sh`, `| python script.py` — executors/processors, not the
  "re-slice the saved output" anti-pattern, so those are ALLOWED.

### SAFETY

  main() wraps parsing + decision in try/except and returns 0 (ALLOW) on ANY
  error. This hook must never break the Bash tool.

## VALIDATION

  test_no_filter_output.py replays this hook against the full transcript history
  (~/.claude/projects/**/*.jsonl, 4147 files, 35k+ unique Bash commands):
  0 exceptions, 0 false positives, 0 cheap-subcommand leaks. Reproduce with:
      python3 ~/.claude/hooks/test_no_filter_output.py --corpus

## LIMITATIONS (known, rare)

  - Command substitution `v=$(curl ... | jq ...)` is intentionally NOT analyzed:
    the `|` inside `$(...)` is protected by the tokenizer, and corpus evidence is
    that this form is value-capture (one scalar into a variable), not the
    inspect-and-re-filter pattern — so blocking it would be a false positive.
  - Subshell grouping `(cmd | filter)` is segmented (paren-aware), but a heavy
    producer that is itself INSIDE the subshell is not recursed into.
  - A here-doc whose closing delimiter never appears, or other unbalanced quoting,
    is consumed to end-of-string (degrades to ALLOW; never raises).
  All of these fall through to ALLOW (fail-open in spirit).

## TUNING

  Edit the tables below (HEAVY_BARE, HEAVY_SUB, HEAVY_SUBSUB, SCRIPT_RUNNER_CHEAP,
  ALWAYS_HEAVY, FILTER_TOOLS, _RUNNERS) and re-run the test battery. The capture
  gate (ANTI-PATTERN 2) is tuned via DEV_SINKS, CAPTURE_TOOLS, AUTHORING_EMITTERS,
  and AUTHORING_PASSTHROUGH — destination paths are otherwise NOT scoped, so a
  capture to any real file (incl. project/deliverable paths) is blocked.

## WIRING (for reference, also in `references/claude-settings.json`)

```json file="~/.claude/settings.json"
{
  "permissions": {
    "allow": [
      "Bash(cargo clippy:*)",
      "Bash(cargo +nightly fmt:*)",
      "Bash(cargo check:*)",
      "Bash(git status:*)",
      "Bash(gh repo list:*)",
      "Bash(gh repo view:*)",
      "Bash(bun run test:*)",
      "Bash(AGENT=1 bun run test:*)",
      "Bash(bun test:*)",
      "Bash(AGENT=1 bun test:*)",
      "Bash(bun typecheck:*)",
      "Bash(AGENT=1 bun typecheck:*)",
      "Bash(bun lint:*)",
      "Bash(AGENT=1 bun lint:*)",
      "Bash(bun pm ls:*)"
    ],
    "deny": [],
    "defaultMode": "default"
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/home/openai/agentic-skills/no-filter-heavy-output/scripts/no_filter_heavy_output.py"
          }
        ]
      }
    ]
  }
}
```