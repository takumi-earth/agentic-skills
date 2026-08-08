#!/usr/bin/env python3
r"""
test_no_filter_output.py — tests for no_filter_heavy_output.py (the PreToolUse hook).

DRY BY CONSTRUCTION
  This imports the hook module the harness actually runs (from the same directory)
  and exercises its real decision()/explain() functions. There is NO duplicated
  classification logic here, so the tests can never drift from the hook. The
  false-positive audit reuses hook.explain() (the hook's own single source of truth
  for which stage triggered a block) and the hook's coverage tables.

USAGE
  python3 test_no_filter_output.py            Fast curated unit battery only.
  python3 test_no_filter_output.py --corpus   Unit battery + full replay against
                                              every Bash command in transcript
                                              history (robustness + false-positive
                                              audit + false-negative sweep).
  python3 test_no_filter_output.py --regress  Unit battery + A/B diff vs the
                                              backed-up old hook (.bak) over the
                                              whole corpus: hard-fails if any
                                              command lost a block or changed its
                                              deny message; lists the new blocks.

  Exit code is non-zero if the unit battery fails, or if the corpus replay finds
  an exception, a false positive, or a cheap-subcommand leak. Run it after editing
  the hook's coverage tables.

WHAT --corpus DOES (and why each step exists)
  1. EXTRACT  — walk ~/.claude/projects/**/*.jsonl and ~/.claude/history.jsonl and
                pull every Bash tool_use command (plus whether its result errored).
  2. ROBUSTNESS — run hook.decision() on every unique command, counting exceptions.
                The hook fails open in production, but a raise here means a latent bug.
  3. FALSE-POSITIVE AUDIT — for each BLOCKED command, ask hook.explain() which stage
                it flagged as the heavy producer. Assert every such producer is a
                known-expensive command word, and that NO cheap script-runner
                subcommand (e.g. `npm ls`, `bun pm`) was blocked. This de-risks the
                aggressive script-runner inversion.
  4. FALSE-NEGATIVE CENSUS — a LIST-AGNOSTIC cross-check. For every command the
                hook does NOT block, attribute each pipeline that feeds a downstream
                filter to its PIPELINE-HEAD command word (via the hook's own
                _command_word), drop known-cheap/noise heads, and rank the rest by
                invocations. The old version was a hardcoded regex that shared the
                hook's blind spots (it omitted `just`, `nix`, the third-party
                `cargo-*` tail, …) so those misses were structurally invisible; the
                census instead surfaces the next unknown heavy runner automatically.
                Soft REVIEW warning only — not a hard failure.
"""
import collections
import glob
import importlib.machinery
import importlib.util
import json
import os
import re
import sys

# ── import the hook under test (same directory) ─────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_HOOK_PATH = os.path.join(_HERE, "no_filter_heavy_output.py")
_spec = importlib.util.spec_from_file_location("no_filter_heavy_output", _HOOK_PATH)
hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hook)


# ═══════════════════════════════════════════════════════════════════════════
# 1. CURATED UNIT BATTERY  (one representative per behaviour the hook must have)
# ═══════════════════════════════════════════════════════════════════════════
BLOCK = [
    # compute | filter
    "cargo test | rg error",
    "pytest -v | tail -50",
    "tsc --noEmit | head",
    "make 2>&1 | grep -i error",
    "uv run pytest | rg FAIL",
    "timeout 300 python train.py | grep loss",
    "RUST_LOG=debug cargo test | rg foo",
    # jq/yq/bat/cat/tee as downstream consumers
    "cargo test | jq .",
    "cargo build | bat",
    "cargo test | tee test.log",
    "python train.py | cat",
    # network / API / git-forge | filter
    "curl -s https://api.example.com/data | jq '.items'",
    "gh api /repos/o/r/pulls | jq '.[].number'",
    "glab api projects/123/issues | jq '.[].title'",
    "aws s3 ls | grep bucket",
    "kubectl get pods | grep web",
    "terraform plan | grep resource",
    # SQL / DB | filter
    "psql -c 'SELECT * FROM users' | grep alice",
    "mysql -e 'SHOW TABLES' | grep log",
    "redis-cli KEYS '*' | grep session",
    "mongosh --eval 'db.x.find()' | jq",
    # docker queries
    "docker logs web | grep error",
    "docker inspect web | jq '.[0].State'",
    # multi-pipe: heavy | filter | filter
    "cargo test 2>&1 | rg error | head -20",
    "curl -s url | jq '.items[]' | grep foo",
    "make 2>&1 | grep error | head",
    "kubectl get pods -o json | jq '.items[]' | grep Running",
    "pytest | grep FAIL | wc -l",
    # multi-pipe: heavy in the MIDDLE (cheap | heavy | filter)
    "cat query.sql | psql -f - | grep result",
    "echo 'SELECT 1' | psql | grep x",
    # command-runner wrappers hide the real command (must still be detected)
    "cat urls.txt | xargs curl -s | jq .",
    "sudo -u postgres psql -c 'SELECT 1' | grep x",
    "cat urls | parallel -j4 curl -s | grep ok",
    "env RUST_LOG=debug cargo test | rg fail",
    # corpus-derived: quoted env values, script-runner shorthands, versioned cc
    'RUSTFLAGS="--cfg tokio_unstable --cap-lints=warn" cargo clippy --workspace 2>&1 | tail -20',
    "AGENT=1 bun lint 2>&1 | grep error | wc -l",
    "bun tsc --noEmit 2>&1 | head -80",
    "bun typecheck 2>&1 | tail -20",
    "npm view eslint versions --json | tail -15",
    "gcc-13 -c main.c 2>&1 | grep error",
    "aarch64-linux-gnu-gcc-13 main.c 2>&1 | grep error",
    "AGENT=0 bun test 2>&1 | grep 'error:' | head -10",
    # task-runners: `<runner> <recipe>` runs arbitrary heavy work (the reported gap)
    "just check 2>&1 | tail -5",
    "just lint 2>&1 | grep -E 'a|b' | head -40",
    "just fmt >/dev/null 2>&1 && just check 2>&1 | tail -5 && just lint 2>&1 | tail -8",
    "task build | tail",
    # cargo INVERTED: builtins + the unbounded third-party `cargo-*` tail are heavy
    "cargo tree -d 2>&1 | head -40",
    "cargo update 2>&1 | tail -20",
    "cargo info serde 2>&1 | head",
    "cargo search tokio | head -3",
    "cargo xtask ci 2>&1 | tail",
    "cargo llvm-cov 2>&1 | tail",
    "cargo generate-lockfile 2>&1 | tail -5",
    "cargo fetch 2>&1 | tail",
    "cargo +nightly fmt --check 2>&1 | tail",
    # bounded-subcommand compilers / fetch CLI
    "zig build 2>&1 | head -60",
    "nix build .#pkg 2>&1 | tail -1",
    "nix-build 2>&1 | tail",
    "firecrawl scrape https://x | jq .",
    # Addendum #1: a REAL trailing pipe hidden because the quoted -c/-e body
    # contains a `|` that the old naive splitter fragmented on.
    "python3 -c \"x='a|b'\" | head",
    "node -e \"const x = (1|2)\" | head -5",
    'curl -A "Mozilla|5.0" https://x | sed -n "1,5p"',
    # Addendum #1: a real command AFTER a here-doc (body is inert; the trailing
    # statement is not) — exercises the here-doc boundary handling.
    "cat <<'EOF' >/tmp/f\nhello world\nEOF\ncargo test | tail",
    # Addendum #3: two-level subcommand.
    "nix flake check 2>&1 | tail -10",
    # ── ANTI-PATTERN 2: manual output capture / redirect to a file ──────────
    # out-of-band Read (canonical): output captured to a file to read back
    "git diff --staged > /tmp/x.diff",
    "ls -la > /tmp/listing.txt",
    'cargo clippy --workspace 2>&1 > /tmp/clippy.txt; echo "exit $?"',
    "bun test &>/tmp/test.txt; echo $?",
    # capture into a deliverable / project path (the tool should write it itself)
    "cargo llvm-cov report > cov/summary.txt",
    "git diff > out.diff",
    "curl -s url > out.json",
    # stderr-only / explicit-fd capture
    "cargo clippy 2> /tmp/err.txt; echo $?",
    "pytest 1>/tmp/out.txt",
    # append capture
    "curl -s https://api/x >> /tmp/dump.json",
    # tee to a file (non-heavy producer the pipe gate misses)
    "git diff | tee out.diff",
    "ls | tee /tmp/listing.txt",
    # quoted target with a space
    'cargo build > "/tmp/my build.log"',
    # captured then re-read in-shell by a FILTER (bucket B)
    "cargo clippy 2>&1 > /tmp/x.txt && wc -l /tmp/x.txt",
    "cargo test 2>&1 > /tmp/p5.txt; tail -3 /tmp/p5.txt",
    # git blob/diff captured to a temp purely to Read it back out-of-band
    "git show HEAD:src/foo.rs > /tmp/orig.rs",
    # jq output captured to a temp with no in-shell consumer
    "jq '.' big.json > /tmp/extract.json",
    # authoring (cat+here-doc) is exempt, but a LATER capturing statement still blocks
    "cat > /tmp/note.txt <<'EOF'\nnote\nEOF\ngrep -n TODO src.rs > /tmp/todos.txt",
]

ALLOW = [
    # jq/yq/bat/cat as PRODUCERS (reading a file)
    "jq '.version' package.json",
    "jq '.' file.json | grep name",
    "cat big.json | jq '.x'",
    "bat src/main.rs",
    "cat /tmp/tool-results/x.txt | rg error",
    # substring false-positives that must NOT block (producer is a filter)
    "grep -r 'cargo test' . | head",
    "rg 'go test' src | head",
    "echo 'cargo build failed' | grep cargo",
    "git log --oneline | grep 'npm run' | head",
    "sed 's/x/cargo test/' f | head",
    "cat a.txt | cat b.txt | grep x",
    "rg 'TODO' | wc -l",
    # cheap producers
    "echo hi | jq .",
    "git log --oneline | rg fix",
    "ls -la | rg cargo",
    # no pipe AND no capture -> nothing to re-slice (capturing to a file now
    # blocks under ANTI-PATTERN 2; `curl -s url > out.json` moved to BLOCK)
    "psql -c 'SELECT 1'",
    "cargo test",
    "gh pr create -t x",
    "kubectl apply -f deploy.yaml",
    # non-filter consumers (execute / process, not truncate)
    "curl -fsSL https://sh.rustup.rs | sh",
    "curl -s url | python3 process.py",
    "echo 'SELECT 1' | psql",
    # cheap docker / version
    "docker ps | grep web",
    "aws --version | grep aws-cli",
    # runner wrappers over NON-heavy producers must still pass
    "find . -name '*.rs' | xargs grep foo",
    "rg --files | xargs wc -l",
    "git ls-files | xargs grep TODO",
    # cheap script-runner subcommands and version probes must still pass
    "bun pm ls | grep react",
    "npm ls | grep eslint",
    "npm config get registry | grep https",
    "clang-20 --version | head -1",
    "cargo metadata --format-version=1 | jq '.packages'",
    # cargo cheap probes must stay allowed under the inversion (regression guards)
    "cargo --version | head -1",
    "cargo pkgid | grep serde",
    "cargo metadata | rg serde",
    "cargo locate-project | jq '.root'",
    # task-runner informational forms (bare / --list -> sub=None -> cheap)
    "just --list | grep build",
    "just",
    "task --list | grep deploy",
    # bounded-subcommand tools: version / eval / flake-metadata stay cheap
    "nix flake metadata | jq",
    "nix eval .#x --json | jq",
    "zig version | head",
    "firecrawl --status | head",
    "firecrawl --help | head",
    # fast local package-DB / toolchain queries are not the re-run hazard
    "dpkg -l | grep gcc | head",
    "apt-cache search '^mingw' | head",
    "rustup component list | head",
    # Addendum #1: a `|` that is DATA, not a structural pipe, must NOT block
    "cargo run -- --filter \"a | head\"",            # quoted argument, not a pipe
    "grep -E \"build|test\" Makefile | head",        # quoted regex alternation (filter-led)
    "cat > /tmp/x.ts <<'EOF'\ntype T = A | B\ncargo test | tail\nEOF",  # here-doc body is data
    "ver=$(curl -s https://u | jq -r .v)",           # #2: command-substitution value-capture stays allowed
    # Addendum #3: sibling flake verbs stay cheap
    "nix flake show | head",
    # ── ANTI-PATTERN 2 negatives: NOT an output capture ─────────────────────
    # /dev sinks (discarding) and fd duplications are not captures
    "cargo test > /dev/null 2>&1",
    "make 2>/dev/null",
    "cargo build > /dev/null",
    "gcc -o app main.c 2>&1 >&2",
    # authoring literal content (not capturing a command's output)
    "echo 'PORT=8080' > .env",
    'printf "%s\\n" "$VERSION" > version.txt',
    "cat > /tmp/script.py <<'EOF'\nprint(1)\nEOF",
    "tee config.toml <<'EOF'\nkey = 1\nEOF",
    # file-based IPC: the captured file is fed to a real (non-filter) consumer
    "a.sh > /tmp/a && b.sh > /tmp/b && diff /tmp/a /tmp/b",
    "cargo build --message-format=json > /tmp/b.json && my-tool --input /tmp/b.json",
    # read-modify-write via a temp that IS consumed in-shell (mv) -> IPC, allowed
    "jq '.x = 1' cfg.json > /tmp/cfg.new && mv /tmp/cfg.new cfg.json",
    # here-doc body piped to a tool: the body (with its inert `>`/`|`) is not a redirect
    "cat <<'EOF' | go run /dev/stdin\npackage main\nfunc main() { _ = 1 > 0 }\nEOF",
]


def run_unit():
    fails = 0
    for cmd in BLOCK:
        if hook.decision(cmd) is None:
            print("FAIL (expected BLOCK):", repr(cmd)); fails += 1
    for cmd in ALLOW:
        if hook.decision(cmd) is not None:
            print("FAIL (expected ALLOW):", repr(cmd)); fails += 1
    print(f"unit: BLOCK={len(BLOCK)} ALLOW={len(ALLOW)} "
          f"total={len(BLOCK)+len(ALLOW)} FAILURES={fails}")
    return fails


# ═══════════════════════════════════════════════════════════════════════════
# 2. CORPUS REPLAY  (extract real commands, drive the real hook)
# ═══════════════════════════════════════════════════════════════════════════
PROJECTS_GLOB = os.path.expanduser("~/.claude/projects/**/*.jsonl")
HISTORY_PATH = os.path.expanduser("~/.claude/history.jsonl")


def extract_commands():
    """Stream every transcript and return (cmd_total, cmd_errored, n_files, n_lines).

    cmd_total[command]   = times that exact Bash command appears as a tool_use.
    cmd_errored[command] = times its result had is_error == true (denied/failed).
    Byte-level prefilters keep this cheap over multi-GB transcripts: only parse a
    line if it can possibly carry a Bash tool_use or an errored tool_result.
    """
    files = sorted(glob.glob(PROJECTS_GLOB, recursive=True))
    cmd_total = collections.Counter()
    cmd_errored = collections.Counter()
    id_to_cmd, errored_ids = {}, set()
    n_lines = 0
    for path in files:
        try:
            fh = open(path, "rb")
        except OSError:
            continue
        with fh:
            for raw in fh:
                n_lines += 1
                has_bash = b'"Bash"' in raw
                has_err = (b'"is_error": true' in raw) or (b'"is_error":true' in raw)
                if not (has_bash or has_err):
                    continue
                try:
                    obj = json.loads(raw)
                except Exception:
                    continue
                msg = obj.get("message") if isinstance(obj, dict) else None
                content = msg.get("content") if isinstance(msg, dict) else None
                if not isinstance(content, list):
                    continue
                for b in content:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "tool_use" and b.get("name") == "Bash":
                        c = (b.get("input") or {}).get("command")
                        if isinstance(c, str) and c.strip():
                            cmd_total[c] += 1
                            if b.get("id"):
                                id_to_cmd[b["id"]] = c
                    elif b.get("type") == "tool_result" and b.get("is_error"):
                        if b.get("tool_use_id"):
                            errored_ids.add(b["tool_use_id"])
    for tid, c in id_to_cmd.items():
        if tid in errored_ids:
            cmd_errored[c] += 1
    return cmd_total, cmd_errored, len(files), n_lines


# ── LIST-AGNOSTIC false-negative census ─────────────────────────────────────
# The old cross-check was a hardcoded `_FN_HEAVY` regex — which shared the hook's
# blind spots (it omitted `just`, `task`, `nix`, `zig`, the third-party `cargo-*`
# tail, …), so a whole class of misses was structurally invisible. The census
# instead derives heaviness from the hook's OWN _command_word: for every command
# the hook does not block, it attributes each pipeline that feeds a downstream
# filter to its PIPELINE-HEAD command word, drops known-cheap/noise heads, and
# ranks the rest. The next unknown runner surfaces at the top automatically.

FN_REVIEW_THRESHOLD = 5   # producers feeding a filter this many times warrant a look

# Fast, deterministic LOCAL producers that legitimately pipe into a filter (re-
# running them to re-slice is cheap, so they are NOT the hazard). Listed only to
# keep the census residue short — not part of the hook's coverage.
EXPECTED_CHEAP = {
    # core text / file / stream tools
    "git", "ls", "cat", "echo", "printf", "find", "fd", "fdfind", "grep", "egrep",
    "fgrep", "rg", "ag", "ack", "sed", "awk", "gawk", "cut", "tr", "tac", "nl",
    "comm", "paste", "sort", "uniq", "wc", "head", "tail", "column", "fold", "jq",
    "yq", "bat", "batcat", "tee", "less", "more", "xxd", "od", "strings", "base64",
    "sha256sum", "md5sum", "cksum", "expr", "test", "[",
    # process / system / fs introspection (fast, deterministic)
    "pwd", "date", "env", "printenv", "whoami", "hostname", "uname", "which",
    "type", "command", "basename", "dirname", "realpath", "readlink", "ps", "df",
    "du", "free", "lsblk", "lscpu", "lsof", "id", "groups", "stat", "file",
    "history", "systemctl", "journalctl", "dmesg", "ip", "ss", "netstat", "diff",
    "ssh", "scp", "seq", "yes", "true", "false", "sleep", "loginctl", "pgrep",
    "pkill", "kill", "jobs", "wait", "set", "export", "mapfile", "read", "locale",
    "tput", "getent", "mktemp", "touch", "mkdir", "cp", "mv", "rm", "ln", "chmod",
    "chown", "tree", "ldconfig", "ldd", "readelf", "nm", "objdump", "mokutil",
    # package-DB / toolchain QUERIES (local, fast); installs go through the hook
    "dpkg", "apt-cache", "apt-get", "apt", "update-alternatives", "unzip", "tar",
    "rustup", "brew", "ffmpeg", "ffprobe", "perl", "ruby", "rustc",
    # opaque executors — `bash -c '<cmd>'` runs an arbitrary inner command this
    # analyzer cannot see into (a documented hook LIMITATION, like subshells), so
    # the SHELL itself is not a classifiable producer. Suppressed here only to keep
    # the REVIEW signal meaningful — NOT a claim that they are cheap.
    "bash", "sh", "zsh", "dash", "ksh", "fish",
}
_SHELL_KW = {"do", "done", "for", "then", "fi", "else", "elif", "while", "case",
             "esac", "in", "function", "time", "if", "until", "local", "select"}
_CMD_TOKEN = re.compile(r"^[A-Za-z0-9_.+-]+$")          # a plausible command basename
_CMDSUB_HEAD = re.compile(r"^\s*(?:[A-Za-z_]\w*=)?\$\(")  # `v=$(...)` / `$(...)` head
_REDIR_HEAD = re.compile(r"^\s*\d*[<>]")                # statement fragment starting at a redirect


def _census_producer(stmt_head):
    """Resolve the head stage's command word, or '' to skip it as noise/cheap.
    Skips: command-substitution / redirect fragments, --version/--help probes,
    filter-led pipelines (`grep | head` = allowed slicing), shell keywords,
    implausible tokens, and the EXPECTED_CHEAP baseline."""
    if _CMDSUB_HEAD.match(stmt_head) or _REDIR_HEAD.match(stmt_head):
        return ""
    if hook._VERSION_PROBE.search(stmt_head):
        return ""
    if hook._is_filter(stmt_head):
        return ""
    w = hook._command_word(stmt_head)
    if not w or not _CMD_TOKEN.match(w) or w.startswith("-"):
        return ""
    if w in _SHELL_KW or w in EXPECTED_CHEAP:
        return ""
    return w


def false_negative_census(cmd_total):
    """Counter{producer_word: invocations} + {word: example} over every UNBLOCKED
    command that pipes into a downstream filter, attributed to the pipeline head."""
    census = collections.Counter()
    example = {}
    for c, n in cmd_total.items():
        try:
            if hook.decision(c) is not None:
                continue
        except Exception:
            continue
        for stages in hook._pipelines(c):     # same quote/here-doc-aware segmenter as the hook
            if len(stages) < 2:
                continue
            if not any(hook._is_filter(s) for s in stages[1:]):
                continue
            w = _census_producer(stages[0])
            if w:
                census[w] += n
                example.setdefault(w, " ".join("|".join(stages).split())[:90])
    return census, example


def run_corpus():
    cmd_total, cmd_errored, n_files, n_lines = extract_commands()
    uniq = list(cmd_total)

    # --- robustness + verdict (drive the REAL hook) -------------------------
    exceptions, blocked = [], []
    for c in uniq:
        try:
            if hook.decision(c) is not None:
                blocked.append(c)
        except Exception as e:           # pragma: no cover - must never happen
            exceptions.append((c, repr(e)))

    # --- false-positive audit (reuse hook.explain — single source of truth) --
    expected = (set(hook.HEAVY_BARE) | set(hook.HEAVY_SUB)
                | set(hook.ALWAYS_HEAVY) | set(hook.SCRIPT_RUNNER_CHEAP))
    heavy_words = collections.Counter()
    suspicious, cheap_leak = [], []
    for c in blocked:
        hit = hook.explain(c)
        if not hit:
            continue
        hw = hit["heavy"][2]
        heavy_words[hw] += 1
        if not (hw in expected or hook._PY.match(hw) or hook._COMPILER.match(hw)):
            suspicious.append((c, hw))
        cheap = hook.SCRIPT_RUNNER_CHEAP.get(hw)
        if cheap is not None:
            sub = hook._subcommand(hit["heavy"][1], hw)
            if sub in cheap:
                cheap_leak.append((c, hw, sub))

    # --- false-negative census (list-agnostic; replaces the keyword sweep) ----
    census, census_ex = false_negative_census(cmd_total)
    review = [(w, n) for w, n in census.most_common()
              if n >= FN_REVIEW_THRESHOLD and w not in expected and w not in EXPECTED_CHEAP]

    blocked_inv = sum(cmd_total[c] for c in blocked)
    only_ran = sum(1 for c in blocked if cmd_total[c] and not cmd_errored.get(c))

    print()
    print("=== CORPUS ===")
    print(f"transcript files       : {n_files}")
    print(f"lines scanned          : {n_lines}")
    print(f"Bash tool_use (total)  : {sum(cmd_total.values())}")
    print(f"Bash tool_use (unique) : {len(uniq)}")
    print()
    print("=== ROBUSTNESS ===")
    print(f"exceptions in decision(): {len(exceptions)}")
    for c, e in exceptions[:10]:
        print("   EXC", e, "::", repr(c)[:120])
    print()
    print("=== VERDICT ===")
    print(f"unique BLOCKED    : {len(blocked)} / {len(uniq)}")
    print(f"invocations BLOCKED: {blocked_inv} / {sum(cmd_total.values())}")
    print(f"  of which only ever EXECUTED historically (real wasted re-runs): {only_ran}")
    print()
    print("=== FALSE-POSITIVE AUDIT (via hook.explain) ===")
    print("heavy producer words among blocks:",
          ", ".join(f"{w}({n})" for w, n in heavy_words.most_common(15)))
    print(f"SUSPICIOUS producers (unexpected word): {len(suspicious)}")
    for c, hw in suspicious[:15]:
        print(f"   heavy={hw!r} :: {' '.join(c.split())[:140]}")
    print(f"CHEAP-SUBCOMMAND LEAKS (bug): {len(cheap_leak)}")
    for c, hw, sub in cheap_leak[:15]:
        print(f"   {hw} {sub} :: {' '.join(c.split())[:140]}")
    print()
    print("=== FALSE-NEGATIVE CENSUS (list-agnostic; head-of-pipe producer) ===")
    print("Producer command words feeding a downstream filter that the hook does NOT")
    print("block, minus known-cheap/noise, ranked by invocations. Derived from the")
    print("hook's own _command_word, so the NEXT unknown runner (the next `just`)")
    print("surfaces here automatically — no hardcoded list to keep in sync.")
    for w, n in census.most_common(25):
        flag = ("  <-- REVIEW (unknown producer)"
                if (n >= FN_REVIEW_THRESHOLD and w not in expected and w not in EXPECTED_CHEAP)
                else "")
        print(f"  {n:5}  {w:18}{flag}  e.g. {census_ex[w]}")
    if review:
        print(f"\nREVIEW: {len(review)} high-frequency producer(s) the hook does not "
              f"classify — confirm each is genuinely cheap, else add it to the hook's "
              f"coverage tables:")
        for w, n in review:
            print(f"   {w} ({n})  e.g. {census_ex[w]}")
    else:
        print("\nREVIEW: none — every frequent filtered producer is either blocked "
              "or a known-cheap local query.")

    # corpus is a hard failure only on exceptions, false positives, or leaks
    bad = len(exceptions) + len(suspicious) + len(cheap_leak)
    print(f"\ncorpus: hard-failures={bad} (exceptions+suspicious+cheap-leaks)")
    return bad


# ═══════════════════════════════════════════════════════════════════════════
# 3. A/B REGRESSION DIFF  (proves the existing gate's verdicts are unchanged)
# ═══════════════════════════════════════════════════════════════════════════
def run_regress():
    """Load the backed-up old hook and diff its verdict against the live hook over
    every corpus command. Hard-fails on any command that LOST a block
    (DENY->ALLOW) or whose deny message CHANGED; lists the new blocks
    (ALLOW->DENY) — the capture-gate additions — for one-by-one audit."""
    bak = _HOOK_PATH + ".bak"
    print("\n=== REGRESS (A/B vs no_filter_heavy_output.py.bak) ===")
    if not os.path.exists(bak):
        print("no baseline backup at", bak, "-- skipped (cannot prove non-regression)")
        return 1
    loader = importlib.machinery.SourceFileLoader("baseline_hook", bak)
    spec = importlib.util.spec_from_loader("baseline_hook", loader)
    base = importlib.util.module_from_spec(spec)
    loader.exec_module(base)

    cmd_total, _err, n_files, _lines = extract_commands()
    lost, changed, added, exc = [], [], [], 0
    for c in cmd_total:
        try:
            old = base.decision(c)
        except Exception:
            old = None
        try:
            new = hook.decision(c)
        except Exception:
            exc += 1
            continue
        if old is not None and new is None:
            lost.append(c)
        elif old is not None and new is not None and old != new:
            changed.append(c)
        elif old is None and new is not None:
            added.append(c)

    print(f"corpus files             : {n_files}")
    print(f"unique commands          : {len(cmd_total)}")
    print(f"LOST blocks (DENY->ALLOW): {len(lost)}   <-- MUST be 0")
    for c in lost[:25]:
        print("   LOST", " ".join(c.split())[:140])
    print(f"CHANGED reason (old DENY): {len(changed)}   <-- MUST be 0")
    for c in changed[:25]:
        print("   CHG ", " ".join(c.split())[:140])
    print(f"exceptions in new hook   : {exc}   <-- MUST be 0")
    print(f"NEW blocks (ALLOW->DENY) : {len(added)}   (capture-gate additions — audit these)")
    for c in added[:80]:
        print("   NEW ", " ".join(c.split())[:140])

    bad = len(lost) + len(changed) + exc
    print(f"\nregress: hard-failures={bad} (lost+changed+exceptions); "
          f"new-blocks={len(added)} (informational)")
    return bad


def main():
    fails = run_unit()
    bad = run_corpus() if "--corpus" in sys.argv else 0
    reg = run_regress() if "--regress" in sys.argv else 0
    sys.exit(1 if (fails or bad or reg) else 0)


if __name__ == "__main__":
    main()
