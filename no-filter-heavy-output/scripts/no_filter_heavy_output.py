#!/usr/bin/env python3
r"""
no_filter_heavy_output.py — Claude Code PreToolUse(Bash) gate.

═══════════════════════════════════════════════════════════════════════════════
WHAT IT DOES
═══════════════════════════════════════════════════════════════════════════════
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

WHY (the problem this solves)
-----------------------------
Filtering an expensive command's output AT THE PIPE couples slicing to
execution. When the filter is wrong, the whole expensive command is re-run to
re-slice — recompiling, re-testing, or re-hitting a DB/API (latency, load, rate
limits; a query may even return different data each run). Prose guidance
(CLAUDE.md) and blunt permission deny-rules both failed at stopping this: prose
loses to the model's priors at generation time; broad/mute deny-rules just get
retried around. A PreToolUse hook intercepts deterministically and — the key
difference from a deny-rule — its rejection message carries the *alternative*, so
the agent redirects instead of retrying.

═══════════════════════════════════════════════════════════════════════════════
DESIGN
═══════════════════════════════════════════════════════════════════════════════
PIPELINE-AWARE, classifying by COMMAND WORD (never substring match).

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

WHAT COUNTS AS "HEAVY" (a producer not worth re-running)
--------------------------------------------------------
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

WHAT COUNTS AS A "FILTER" (a consumer that slices/truncates)
------------------------------------------------------------
  FILTER_TOOLS: grep/rg/head/tail/sed/awk/wc/cut/sort/uniq/less/column/... PLUS
  jq/yq/bat/cat/tee.  jq/cat/bat/tee are filters ONLY as a DOWNSTREAM stage; as
  the FIRST command they read a file and are cheap (`jq . file`, `cat f | rg`).
  NOT filters: `| sh`, `| python script.py` — executors/processors, not the
  "re-slice the saved output" anti-pattern, so those are ALLOWED.

SAFETY
------
  main() wraps parsing + decision in try/except and returns 0 (ALLOW) on ANY
  error. This hook must never break the Bash tool.

VALIDATION
----------
  test_no_filter_output.py replays this hook against the full transcript history
  (~/.claude/projects/**/*.jsonl, 4147 files, 35k+ unique Bash commands):
  0 exceptions, 0 false positives, 0 cheap-subcommand leaks. Reproduce with:
      python3 ~/.claude/hooks/test_no_filter_output.py --corpus

LIMITATIONS (known, rare)
-------------------------
  - Command substitution `v=$(curl ... | jq ...)` is intentionally NOT analyzed:
    the `|` inside `$(...)` is protected by the tokenizer, and corpus evidence is
    that this form is value-capture (one scalar into a variable), not the
    inspect-and-re-filter pattern — so blocking it would be a false positive.
  - Subshell grouping `(cmd | filter)` is segmented (paren-aware), but a heavy
    producer that is itself INSIDE the subshell is not recursed into.
  - A here-doc whose closing delimiter never appears, or other unbalanced quoting,
    is consumed to end-of-string (degrades to ALLOW; never raises).
  All of these fall through to ALLOW (fail-open in spirit).

TUNING
------
  Edit the tables below (HEAVY_BARE, HEAVY_SUB, HEAVY_SUBSUB, SCRIPT_RUNNER_CHEAP,
  ALWAYS_HEAVY, FILTER_TOOLS, _RUNNERS) and re-run the test battery. The capture
  gate (ANTI-PATTERN 2) is tuned via DEV_SINKS, CAPTURE_TOOLS, AUTHORING_EMITTERS,
  and AUTHORING_PASSTHROUGH — destination paths are otherwise NOT scoped, so a
  capture to any real file (incl. project/deliverable paths) is blocked.

WIRING (for reference)
----------------------
  ~/.claude/settings.json:
    "hooks": { "PreToolUse": [ { "matcher": "Bash",
                 "hooks": [ { "type": "command",
                              "command": "/home/openai/.claude/hooks/no_filter_heavy_output.py" } ] } ] }
"""
import json
import re
import sys

# ═══════════════════════════════════════════════════════════════════════════
# COVERAGE TABLES  (the only things you normally need to edit)
# ═══════════════════════════════════════════════════════════════════════════

# Bare commands that are themselves expensive, keyed by command word.
HEAVY_BARE = {
    # compilers (versioned/cross forms also matched by _COMPILER below)
    "rustc", "cc", "c++", "gcc", "g++", "clang", "clang++",
    # JS/TS toolchain
    "tsc", "eslint", "prettier", "biome", "vitest", "jest", "vite", "webpack",
    "esbuild", "rollup", "tsx",
    # runtimes / interpreters
    "node", "deno",
    # python tooling
    "pytest", "mypy", "ruff", "pyright", "pylint", "flake8", "black", "coverage",
    "tox", "nox",
    # go / build systems
    "golangci-lint", "make", "cmake", "ninja", "bazel", "meson", "gradle", "mvn",
    "nix-build", "nix-shell",
    # network / API fetchers
    "curl", "wget", "http", "https", "xh", "xhs", "httpie",
    # git-forge / cloud / cluster CLIs
    "gh", "glab", "doctl", "aws", "gcloud", "az", "kubectl", "oc", "helm", "terraform",
    # SQL / database clients
    "psql", "mysql", "mariadb", "sqlite3", "duckdb", "mongo", "mongosh", "redis-cli",
    "clickhouse-client", "clickhouse", "cqlsh", "cockroach", "influx", "usql",
    "surreal", "pgcli", "mycli",
}

# Managers heavy ONLY for these subcommands (cheap otherwise — so
# `cargo metadata | jq`, `go env | grep`, `docker ps | grep` stay ALLOWED).
HEAVY_SUB = {
    # NOTE: cargo is intentionally NOT here — it is an INVERTED runner (see
    # SCRIPT_RUNNER_CHEAP). Its third-party subcommand tail (xtask, llvm-cov,
    # machete, upgrade, dupes, xclippy, nextest, …) is unbounded, so a positive
    # list can't keep up; cargo is heavy for EVERY subcommand except a tiny cheap
    # allowlist.
    "deno": {"test", "run", "check", "bench", "compile", "lint", "task", "bundle"},
    "go": {"test", "build", "run", "vet", "install", "generate"},
    "uv": {"run", "sync", "build", "lock", "pip", "add", "remove", "tool", "export", "tree"},
    "pip": {"install", "download", "wheel"},
    "pip3": {"install", "download", "wheel"},
    "docker": {"build", "buildx", "compose", "logs", "inspect"},
    # compilers / build tools with a BOUNDED heavy-subcommand set (version/info/fmt
    # and JSON probes like `nix flake metadata | jq`, `zig version | head` stay cheap).
    "zig": {"build", "test", "run", "build-exe", "build-lib", "build-obj", "cc",
            "c++", "translate-c", "ast-check"},
    "nix": {"build", "run", "develop", "shell", "profile", "bundle", "search"},
    # firecrawl scrape/fetch CLI: network subcommands re-hit the API on re-slice;
    # `firecrawl --status` / `--help` resolve to sub=None and stay cheap.
    "firecrawl": {"scrape", "crawl", "search", "map", "extract", "batch", "research"},
}

# Two-level subcommands: heavy ONLY for a specific SECOND-level verb, so sibling
# verbs stay cheap. e.g. `nix flake check` re-evaluates/builds all flake outputs
# (heavy), but `nix flake metadata|show|info | jq` are cheap inspections. Consulted
# in _is_heavy AFTER HEAVY_SUB. `update/lock/archive/prefetch` re-resolve or
# download; `check` is the one actually seen feeding a filter in the corpus.
HEAVY_SUBSUB = {
    "nix": {"flake": {"check", "update", "lock", "archive", "prefetch"}},
}

# INVERTED runners — heavy for ANY subcommand EXCEPT the cheap allowlist. Empty
# set => every non-flag subcommand is heavy (flags resolve to sub=None -> cheap).
# Covers: package-script runners bun/npm/yarn/pnpm (lint/typecheck/tsc/view/test/
# run/<script> heavy); cargo (its third-party `cargo-*` tail is unbounded, so only
# the fast JSON/path probes stay cheap); task-runners just/task (any recipe name
# is heavy; bare runner and --list/-l/--summary are cheap).
SCRIPT_RUNNER_CHEAP = {
    "bun":  {"pm", "init", "create", "link", "unlink", "completions", "upgrade",
             "help", "repl", "--version", "--help"},
    "npm":  {"ls", "list", "init", "config", "prefix", "root", "bin", "whoami", "ping",
             "help", "why", "link", "unlink", "login", "logout", "star", "unstar",
             "fund", "docs", "repo", "home", "edit", "get", "set", "version", "pkg",
             "org", "team", "access", "profile", "owner", "completion", "doctor"},
    "yarn": {"init", "list", "config", "bin", "cache", "versions", "why", "help",
             "login", "logout", "link", "unlink", "node", "policies", "workspaces"},
    "pnpm": {"ls", "list", "init", "config", "root", "bin", "store", "why", "link",
             "unlink", "help", "env", "setup", "completion"},
    # cargo: heavy for every subcommand except these fast JSON/path probes (+ version/
    # help). Catches builtins tree/update/info/search/fetch/generate-lockfile AND the
    # unbounded third-party tail (xtask/llvm-cov/machete/upgrade/dupes/xclippy/…),
    # while keeping `cargo metadata | jq`, `cargo pkgid | grep` allowed.
    "cargo": {"metadata", "pkgid", "locate-project", "verify-project",
              "read-manifest", "config", "version", "help"},
    # task-runners: `<runner> <recipe>` runs arbitrary heavy work. Empty cheap-set —
    # bare runner / --list / -l / --summary are flags (sub=None -> cheap); only a
    # real recipe/task name (a non-flag token) is heavy.
    "just": set(),
    "task": set(),
}

# Wrappers that run an ARBITRARY command (always treat what they wrap, not them).
ALWAYS_HEAVY = {"npx", "bunx", "pnpx", "dlx"}

# Consumers that slice / truncate / re-render. jq/yq/bat/cat/tee count here ONLY
# as a downstream stage (they are cheap as the FIRST command reading a file).
FILTER_TOOLS = {
    "grep", "egrep", "fgrep", "ggrep", "rg", "ag", "ack",
    "head", "ghead", "tail", "gtail",
    "sed", "gsed", "awk", "gawk",
    "wc", "gwc", "cut", "gcut", "sort", "gsort", "uniq", "guniq",
    "less", "more", "fold", "column",
    "jq", "yq", "bat", "batcat", "cat", "tee",
}

# Command-runner wrappers: word -> the options that consume the NEXT token as a
# value. Peeling these is what makes `... | xargs curl | jq` see `curl`,
# `sudo -u pg psql` see `psql`, `timeout 300 cargo test` see `cargo`.
_RUNNERS = {
    "sudo":     {"-u", "-g", "-U", "-p", "-C", "-r", "-t", "--user", "--group"},
    "env":      {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"},
    "xargs":    {"-n", "-P", "-I", "-i", "-d", "-L", "-l", "-s", "-a", "-E", "-e",
                 "--max-args", "--max-procs", "--replace", "--delimiter",
                 "--max-lines", "--arg-file", "--eof"},
    "parallel": {"-j", "-P", "-n", "-N", "--jobs", "--max-procs"},
    "timeout":  {"-s", "--signal", "-k", "--kill-after"},
    "stdbuf":   {"-i", "-o", "-e", "--input", "--output", "--error"},
    "nice":     {"-n", "--adjustment"},
    "ionice":   {"-c", "-n", "-p"},
    "taskset":  {"-c", "--cpu-list", "-p"},
    "watch":    {"-n", "--interval"},
    "chrt": set(), "nohup": set(), "setsid": set(), "time": set(),
    "command": set(), "builtin": set(), "exec": {"-a"},
}
_RUNNER_DURATION = {"timeout"}   # also takes one bare positional (a duration)

# ── ANTI-PATTERN 2 tables: manual output capture / redirect to a file ───────
# Capture DESTINATIONS that are not a real file (so not the anti-pattern): /dev
# sinks (output is discarded). fd duplications (`2>&1`, `>&2`) are handled in code.
DEV_SINKS = {
    "/dev/null", "/dev/stdout", "/dev/stderr", "/dev/tty",
    "/dev/zero", "/dev/random", "/dev/urandom",
}
# Tee-like tools that WRITE stdin to a file argument (a capture, not a pipe filter).
CAPTURE_TOOLS = {"tee", "sponge"}
# Producers that emit LITERAL content, so `echo x > f` / `printf … > f` is file
# AUTHORING, not output capture. Pass-through producers (cat/tee) are authoring
# only when fed by a here-doc / here-string (`cat > f <<EOF … EOF`).
AUTHORING_EMITTERS = {"echo", "printf"}
AUTHORING_PASSTHROUGH = {"cat", "tee"}

# ═══════════════════════════════════════════════════════════════════════════
# CLASSIFICATION  (command-word resolution; see DESIGN above)
# ═══════════════════════════════════════════════════════════════════════════

# Leading `VAR=val VAR2="a b" ` env-assignment prefix (quote-aware).
_ENV_PREFIX = re.compile(r'^(?:[A-Za-z_]\w*=(?:"[^"]*"|\'[^\']*\'|[^\s]*)\s+)+')
_ENV = re.compile(r"^[A-Za-z_]\w*=")
_VERSION_PROBE = re.compile(r"(?:^|\s)--(?:version|help)\b")
_PY = re.compile(r"python(?:\d[\d.]*)?$")
# versioned / cross-prefixed compilers: gcc-13, clang++-20, aarch64-linux-gnu-gcc-13
_COMPILER = re.compile(r"(?:^|.*-)(?:gcc|g\+\+|clang|clang\+\+|cc|c\+\+)(?:-\d+(?:\.\d+)?)?$")


def _strip_amp(s):
    """Drop a leading '&' left over when a stage came from splitting '|&'."""
    s = s.strip()
    return s[1:].lstrip() if s.startswith("&") else s


def _command_word(stage):
    """Resolve a stage's effective command token (basename) by stripping env
    assignments (quote-aware) and peeling command-runner wrappers. '' if none.
    e.g. 'RUSTFLAGS="-Cx" timeout 5 cargo test' -> 'cargo';  'xargs -n1 curl' -> 'curl'."""
    s = _ENV_PREFIX.sub("", _strip_amp(stage))
    toks = s.split()
    i, guard = 0, 0
    while i < len(toks) and guard < 64:          # guard: defensive bound on wrapper nesting
        guard += 1
        while i < len(toks) and _ENV.match(toks[i]):     # bare FOO=bar (e.g. after `env`)
            i += 1
        if i >= len(toks):
            return ""
        w = toks[i].rsplit("/", 1)[-1]           # basename: /usr/bin/psql -> psql
        runner = _RUNNERS.get(w)
        if runner is None:
            return w                             # not a wrapper -> this is the command
        i += 1                                   # skip the wrapper word ...
        while i < len(toks) and toks[i].startswith("-"):   # ... and its own flags
            i += 2 if (toks[i] in runner and "=" not in toks[i]) else 1
        if w in _RUNNER_DURATION and i < len(toks) and re.match(r"^[0-9]", toks[i]):
            i += 1                               # e.g. the DURATION positional of `timeout`
        # loop: the next token may be a nested wrapper or the real command
    return ""


def _subcommand(stage, word):
    """First non-flag, non-toolchain token after the manager `word` (e.g. the
    'test' in 'cargo test', the 'view' in 'npm view'). None if absent."""
    toks = _ENV_PREFIX.sub("", _strip_amp(stage)).split()
    for k, t in enumerate(toks):
        if t.rsplit("/", 1)[-1] == word:
            for t2 in toks[k + 1:]:
                if t2.startswith("-") or t2.startswith("+"):   # skip flags and +toolchain
                    continue
                return t2
            return None
    return None


def _subcommands(stage, word, k=2):
    """The first `k` non-flag, non-toolchain tokens after `word` (e.g.
    ['flake', 'check'] for 'nix flake check'). Used for two-level HEAVY_SUBSUB
    resolution. Returns as many as exist (possibly fewer than k, or [])."""
    toks = _ENV_PREFIX.sub("", _strip_amp(stage)).split()
    out = []
    for idx, t in enumerate(toks):
        if t.rsplit("/", 1)[-1] == word:
            for t2 in toks[idx + 1:]:
                if t2.startswith("-") or t2.startswith("+"):   # skip flags and +toolchain
                    continue
                out.append(t2)
                if len(out) >= k:
                    break
            break
    return out


def _is_heavy(stage):
    """True if `stage`'s command is an expensive producer (see DESIGN)."""
    word = _command_word(stage)
    if not word:
        return False
    if _VERSION_PROBE.search(stage):             # `--version` / `--help` are cheap
        return False
    if word in ALWAYS_HEAVY or word in HEAVY_BARE or _PY.match(word) or _COMPILER.match(word):
        return True
    cheap = SCRIPT_RUNNER_CHEAP.get(word)
    if cheap is not None:                        # inverted runner: heavy unless cheap sub
        sub = _subcommand(stage, word)
        return sub is not None and sub not in cheap
    subs = HEAVY_SUB.get(word)
    if subs is not None and _subcommand(stage, word) in subs:
        return True                              # positive-list manager
    subsub = HEAVY_SUBSUB.get(word)
    if subsub is not None:                        # two-level, e.g. `nix flake check`
        sc = _subcommands(stage, word, 2)
        if len(sc) >= 2 and sc[0] in subsub and sc[1] in subsub[sc[0]]:
            return True
    return False


def _is_filter(stage):
    """True if `stage`'s command is a slicing/truncating consumer."""
    return _command_word(stage) in FILTER_TOOLS


# ═══════════════════════════════════════════════════════════════════════════
# SEGMENTATION  (quote / paren / here-doc-aware; decides which | && ; \n are
# STRUCTURAL operators vs. DATA inside quoting/nesting — see DESIGN step 1)
# ═══════════════════════════════════════════════════════════════════════════

_HEREDOC_DELIM = re.compile(r"\w+")


def _scan_segments(s):
    """Walk `s` once, yielding (segment, operator) where operator is one of
    '|', '||', '&&', ';', '\\n', or '' (final). A control operator splits ONLY at
    TOP LEVEL: a `|`/`&&`/`;`/newline inside '…', "…", a backslash escape,
    `$(…)`/`(…)`, `${…}`, backticks, or a here-doc body is DATA, not a split
    point. Bounded tokenizer, not a shell interpreter; any unterminated construct
    is consumed to end-of-string (fail-safe)."""
    seg = []
    i, n = 0, len(s)
    in_s = in_d = btick = False
    depth = bdepth = 0                 # () / $() paren depth ; ${} brace depth
    heredocs = []                      # FIFO queue of (delimiter, strip_leading_tabs)

    def _consume_heredocs(i):
        # i points at the newline that STARTS the first body. Consume that newline
        # and every body line through each closing delimiter (FIFO), all inert
        # (never scanned for operators). Leave i AT the newline that follows the
        # LAST delimiter line, so the caller treats it as a normal statement
        # boundary (a command may follow the here-doc on the next line).
        seg.append("\n")
        i += 1
        while heredocs:
            delim, dash = heredocs.pop(0)
            while i < n:
                e = s.find("\n", i)
                line = s[i:(e if e != -1 else n)]
                chk = line.lstrip("\t") if dash else line
                if chk.strip() == delim:
                    seg.append(line)                    # delimiter line, sans newline
                    i = e if e != -1 else n             # leave i AT its newline (or end)
                    break
                seg.append(s[i:(e + 1 if e != -1 else n)])   # ordinary body line + newline
                i = e + 1 if e != -1 else n
                if e == -1:
                    break
            else:
                break
            if heredocs and i < n and s[i] == "\n":   # newline between stacked here-docs
                seg.append("\n"); i += 1
        return i

    while i < n:
        c = s[i]
        nxt = s[i + 1] if i + 1 < n else ""
        if in_s:                                 # single quotes: literal until next '
            seg.append(c)
            if c == "'":
                in_s = False
            i += 1
            continue
        if c == "\\":                            # backslash escapes the next char
            seg.append(c)
            if i + 1 < n:
                seg.append(s[i + 1]); i += 2
            else:
                i += 1
            continue
        if in_d:                                 # double quotes: $()/`` still active
            if c == '"':
                in_d = False; seg.append(c); i += 1; continue
            if c == "$" and nxt == "(":
                depth += 1; seg.append(c); seg.append(nxt); i += 2; continue
            if c == "`":
                btick = not btick; seg.append(c); i += 1; continue
            if c == ")" and depth > 0:
                depth -= 1; seg.append(c); i += 1; continue
            seg.append(c); i += 1; continue
        # not inside any quote -------------------------------------------------
        if (depth == 0 and bdepth == 0 and not btick
                and c == "<" and nxt == "<"):    # here-doc start: <<WORD / <<-'WORD'
            j = i + 2
            dash = j < n and s[j] == "-"
            if dash:
                j += 1
            while j < n and s[j] in " \t":
                j += 1
            q = ""
            if j < n and s[j] in "'\"":
                q = s[j]; j += 1
            m = _HEREDOC_DELIM.match(s, j)
            if m:
                delim = m.group(0); j = m.end()
                if q and j < n and s[j] == q:
                    j += 1
                heredocs.append((delim, dash))
                seg.append(s[i:j]); i = j; continue
            # `<<` not followed by a delimiter word -> fall through, treat literally
        if c == "'":
            in_s = True; seg.append(c); i += 1; continue
        if c == '"':
            in_d = True; seg.append(c); i += 1; continue
        if c == "`":
            btick = not btick; seg.append(c); i += 1; continue
        if c == "$" and nxt == "(":
            depth += 1; seg.append(c); seg.append(nxt); i += 2; continue
        if c == "$" and nxt == "{":
            bdepth += 1; seg.append(c); seg.append(nxt); i += 2; continue
        if c == "(":
            depth += 1; seg.append(c); i += 1; continue
        if c == ")" and depth > 0:
            depth -= 1; seg.append(c); i += 1; continue
        if c == "}" and bdepth > 0:
            bdepth -= 1; seg.append(c); i += 1; continue
        if depth == 0 and bdepth == 0 and not btick:        # TOP LEVEL: operators split
            if c == "\n" and heredocs:
                i = _consume_heredocs(i); continue
            if c == "\n":
                yield "".join(seg), "\n"; seg = []; i += 1; continue
            if c == ";":
                yield "".join(seg), ";"; seg = []; i += 1; continue
            if c == "&" and nxt == "&":
                yield "".join(seg), "&&"; seg = []; i += 2; continue
            if c == "|" and nxt == "|":
                yield "".join(seg), "||"; seg = []; i += 2; continue
            if c == "|":
                yield "".join(seg), "|"; seg = []; i += 1; continue
        seg.append(c); i += 1
    yield "".join(seg), ""


def _pipelines(cmd):
    """Segment `cmd` into STATEMENTS (split on top-level && || ; newline), each a
    list of STAGES (split on top-level single `|`). `"|".join(stages)` faithfully
    reconstructs the statement text. Quote / paren / here-doc aware."""
    stmts, stages = [], []
    for seg, op in _scan_segments(cmd):
        stages.append(seg)
        if op == "|":
            continue                              # same pipeline, next stage
        stmts.append(stages); stages = []         # &&/||/;/newline/end => boundary
    if stages:
        stmts.append(stages)
    return stmts


# ═══════════════════════════════════════════════════════════════════════════
# OUTPUT CAPTURE  (ANTI-PATTERN 2: redirecting/tee-ing a command's output to a
# file the harness already persists, or that the owning tool should write itself)
# ═══════════════════════════════════════════════════════════════════════════

# Token boundary inside a (single) pipeline stage: whitespace or a shell
# metacharacter that ends a word / begins a redirect.
_WORD_STOP = set(" \t\n|&;<>()")


def _unquote(tok):
    """Strip one matching layer of surrounding quotes from a token."""
    tok = tok.strip()
    if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in "'\"":
        return tok[1:-1]
    return tok


def _read_redirect_target(s, j):
    """From index `j` (just past a redirect operator) read the target word.
    Returns (target, is_dup, new_index): target is None if absent; is_dup is True
    for an fd duplication target (`&1`, `&-`) rather than a file. Quote-aware."""
    n = len(s)
    while j < n and s[j] in " \t":
        j += 1
    if j >= n:
        return None, False, j
    if s[j] == "&":                              # fd duplication: >&1, 2>&1, >&-
        k = j + 1
        while k < n and s[k] not in _WORD_STOP:
            k += 1
        return s[j:k], True, k
    if s[j] in "'\"":                            # quoted target (may contain spaces)
        q = s[j]
        k = j + 1
        while k < n and s[k] != q:
            k += 1
        return s[j + 1:k], False, (k + 1 if k < n else k)
    k = j
    while k < n and s[k] not in _WORD_STOP:
        k += 1
    return s[j:k], False, k


def _capture_targets(stage):
    """Scan one pipeline STAGE for top-level output redirects and whether it is
    fed by a here-doc / here-string. Returns (targets, heredoc_fed):
      targets      list of (target_word, is_dup) for each top-level `>`/`>>`/`>|`/
                   `&>`/`&>>`/`N>` redirect (the leading fd is irrelevant to
                   classification); is_dup True for an fd duplication (`2>&1`).
      heredoc_fed  True if a top-level `<<WORD` here-doc or `<<<` here-string feeds
                   the stage (used by the authoring exemption).
    Quote / escape / subshell aware (mirrors _scan_segments); never raises. A
    redirect placed AFTER a here-doc/here-string marker on the line is not seen
    (rare; degrades to allow)."""
    targets = []
    heredoc_fed = False
    i, n = 0, len(stage)
    in_s = in_d = btick = False
    depth = bdepth = 0
    while i < n:
        c = stage[i]
        nxt = stage[i + 1] if i + 1 < n else ""
        if in_s:
            if c == "'":
                in_s = False
            i += 1; continue
        if c == "\\":
            i += 2 if i + 1 < n else 1; continue
        if in_d:
            if c == '"':
                in_d = False; i += 1; continue
            if c == "$" and nxt == "(":
                depth += 1; i += 2; continue
            if c == "`":
                btick = not btick; i += 1; continue
            if c == ")" and depth > 0:
                depth -= 1; i += 1; continue
            i += 1; continue
        if depth == 0 and bdepth == 0 and not btick and c == "\n":
            break                                # end of the command line; any
            # following line is a here-doc body / inert text (a here-doc body
            # split past an upstream `|` lands in this stage with no `<<` marker),
            # and redirects only ever appear on the command line itself.
        if depth == 0 and bdepth == 0 and not btick and c == "<" and nxt == "<":
            heredoc_fed = True; break            # here-doc / here-string body is inert
        if c == "'":
            in_s = True; i += 1; continue
        if c == '"':
            in_d = True; i += 1; continue
        if c == "`":
            btick = not btick; i += 1; continue
        if c == "$" and nxt == "(":
            depth += 1; i += 2; continue
        if c == "$" and nxt == "{":
            bdepth += 1; i += 2; continue
        if c == "(":
            depth += 1; i += 1; continue
        if c == ")" and depth > 0:
            depth -= 1; i += 1; continue
        if c == "}" and bdepth > 0:
            bdepth -= 1; i += 1; continue
        if depth == 0 and bdepth == 0 and not btick:
            if c == "&" and nxt == ">":          # combined: &> / &>>  (NOT && / bare &)
                j = i + 2
                if j < n and stage[j] == ">":
                    j += 1
                tgt, is_dup, j = _read_redirect_target(stage, j)
                if tgt is not None:
                    targets.append((tgt, is_dup))
                i = j; continue
            if c == ">":                         # `>` / `>>` / `>|`  (leading fd ignored)
                j = i + 1
                if j < n and stage[j] == ">":
                    j += 1
                if j < n and stage[j] == "|":
                    j += 1
                tgt, is_dup, j = _read_redirect_target(stage, j)
                if tgt is not None:
                    targets.append((tgt, is_dup))
                i = j; continue
        i += 1
    return targets, heredoc_fed


def _tee_targets(stage):
    """File operands of a `tee`/`sponge` capture stage (its non-flag arguments)."""
    if _command_word(stage) not in CAPTURE_TOOLS:
        return []
    toks = _ENV_PREFIX.sub("", _strip_amp(stage)).split()
    out, seen = [], False
    for t in toks:
        if not seen:
            if t.rsplit("/", 1)[-1] in CAPTURE_TOOLS:
                seen = True
            continue
        if t.startswith("-"):
            continue
        out.append(_unquote(t))
    return out


def _is_excepted_target(target, is_dup):
    """True if `target` is NOT a real-file capture: an fd duplication (`&1`) or a
    /dev sink (`/dev/null`, `/dev/stderr`, `/dev/fd/N`, …). `/dev/shm/x` is a real
    tmpfs file, so it is NOT excepted."""
    if is_dup or target.startswith("&"):
        return True
    t = _unquote(target)
    return t in DEV_SINKS or t.startswith("/dev/fd/")


def _is_authoring(stage, heredoc_fed):
    """True if the stage WRITES literal content rather than capturing a command's
    output: an `echo`/`printf` literal emitter with no command substitution, or a
    pass-through `cat`/`tee` fed by a here-doc / here-string."""
    word = _command_word(stage)
    if word in AUTHORING_EMITTERS:
        return "$(" not in stage and "`" not in stage
    if word in AUTHORING_PASSTHROUGH and heredoc_fed:
        return True
    return False


def _consumers_of(target, prod_idx, all_stages):
    """Scan the OTHER stages for one that READS `target` as a whole-token argument
    (excluding a stage's own redirect/tee targets, so a re-write is not a read).
    Returns (consumed_by_filter, consumed_by_real)."""
    norm = _unquote(target)
    by_filter = by_real = False
    for idx, st in enumerate(all_stages):
        if idx == prod_idx:
            continue
        own = {_unquote(t) for t, _ in _capture_targets(st)[0]} | {_unquote(t) for t in _tee_targets(st)}
        toks = {_unquote(tok) for tok in st.split()} - own
        if norm in toks:
            if _is_filter(st):
                by_filter = True
            else:
                by_real = True
    return by_filter, by_real


def capture_explain(cmd):
    """Core analyzer for ANTI-PATTERN 2. Return None if `cmd` has no offending
    capture, else a dict describing the FIRST one:

        {"statement": <stage str>, "producer": <command word>,
         "target": <captured file>, "consumed_by_filter": <bool>}

    BLOCK iff a stage captures output (`>`-family or `tee`) to a real file that is
    NOT authoring and is NOT consumed in-shell by a real (non-filter) command."""
    if not cmd or not cmd.strip():
        return None
    all_stages = [st for stmt in _pipelines(cmd) for st in stmt]
    for idx, stage in enumerate(all_stages):
        targets, heredoc_fed = _capture_targets(stage)
        captures = list(targets) + [(t, False) for t in _tee_targets(stage)]
        if not captures or _is_authoring(stage, heredoc_fed):
            continue
        for target, is_dup in captures:
            if _is_excepted_target(target, is_dup):
                continue
            by_filter, by_real = _consumers_of(target, idx, all_stages)
            if by_real and not by_filter:        # file-based IPC to a real consumer
                continue
            return {
                "statement": stage,
                "producer": _command_word(stage),
                "target": _unquote(target),
                "consumed_by_filter": by_filter,
            }
    return None


# ═══════════════════════════════════════════════════════════════════════════
# DECISION  (single source of truth — decision() and the tests both use explain())
# ═══════════════════════════════════════════════════════════════════════════

def explain(cmd):
    """Core analyzer. Return None if `cmd` is ALLOWED, else a dict describing the
    FIRST offending pipeline:

        {"statement": <str>,
         "heavy":  (index, stage_str, command_word),   # the expensive producer
         "filter": (index, stage_str, command_word)}   # the downstream filter

    decision() is a thin wrapper over this, and the test/audit tooling calls
    explain() directly — so the pipeline logic has ONE definition and the tests
    can never drift from what the hook actually does."""
    if not cmd or not cmd.strip():
        return None
    for stages in _pipelines(cmd):
        if len(stages) < 2:
            continue
        heavy_at = None
        for i, stage in enumerate(stages):
            if _is_heavy(stage):
                if heavy_at is None:
                    heavy_at = i
            elif heavy_at is not None and i > heavy_at and _is_filter(stage):
                return {
                    "statement": "|".join(stages),
                    "heavy": (heavy_at, stages[heavy_at], _command_word(stages[heavy_at])),
                    "filter": (i, stage, _command_word(stage)),
                }
    return None


def decision(cmd):
    """Return the deny-reason string if `cmd` should be blocked, else None.

    Two independent gates. The pipe-filter gate (explain) runs FIRST and its
    verdict/message is returned verbatim when it fires, so its behavior is
    unchanged; otherwise the output-capture gate (capture_explain) runs."""
    if explain(cmd):
        return _reason(cmd)
    if capture_explain(cmd):
        return _reason_capture(cmd)
    return None


def _reason(cmd):
    snippet = cmd.strip()
    if len(snippet) > 200:
        snippet = snippet[:200] + " …"
    return (
        "Don't filter an expensive command's output at the pipe.\n\n"
        f"  {snippet}\n\n"
        "Filtering at the pipe ties slicing to execution, so re-slicing re-runs the "
        "whole command — recompiling, re-testing, or re-hitting the DB/API/network — "
        "the exact waste to avoid (a query can even return different data each run).\n\n"
        "Do this instead:\n"
        "  1. Re-run WITHOUT the pipe (drop the | grep/head/tail/jq/...).\n"
        "  2. The harness auto-saves the FULL output to a temp file and prints its "
        "path in the result.\n"
        "  3. Use the Grep and Read TOOLS on that path to search/slice it — unlimited, "
        "instant, with zero re-runs.\n\n"
        "Slicing an already-saved file is always allowed; only re-running the expensive "
        "command to filter its output is blocked."
    )


def _reason_capture(cmd):
    snippet = cmd.strip()
    if len(snippet) > 200:
        snippet = snippet[:200] + " …"
    hit = capture_explain(cmd)
    target = hit["target"] if hit else "a file"
    return (
        "Don't capture a command's output to a file by hand.\n\n"
        f"  {snippet}\n\n"
        f"This redirects output into `{target}`, but the harness ALREADY saves the FULL "
        "output of every command to a temp file and prints its path in the result — a "
        "manual capture just duplicates that. And for a tool that writes its own output "
        "file (a coverage/report command writing cov/summary.txt), a hand redirect "
        "bypasses the tool's real logic.\n\n"
        "Do this instead:\n"
        "  1. Run the command WITHOUT the redirect.\n"
        "  2. Read the path the harness prints, with the Read/Grep TOOLS — unlimited, "
        "instant, no re-run.\n"
        "  3. For a real deliverable file, let the owning tool write it through its own "
        "interface, or author it with the Write tool.\n\n"
        "Allowed: discarding to /dev/null, fd duplications (2>&1), writing literal content "
        "(echo/printf/here-doc), and feeding the file to another command in the same line."
    )


# ═══════════════════════════════════════════════════════════════════════════
# HOOK ENTRYPOINT  (reads the PreToolUse event JSON on stdin)
# ═══════════════════════════════════════════════════════════════════════════

def main():
    try:
        data = json.load(sys.stdin)
        cmd = (data.get("tool_input") or {}).get("command") or ""
        reason = decision(cmd)
    except Exception:
        return 0  # fail open — this hook must never break the Bash tool
    if reason:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
