#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf '%s\n' \
    'usage: verify-test-parity-ledger.sh --ledger PATH --baseline REF [--repo PATH]' \
    '' \
    'Require every removed Rust test to name existing replacements or an evidenced production capability removal.'
}

baseline=''
repository='.'
ledger=''

while (($# > 0)); do
  case "$1" in
    --baseline)
      if (($# < 2)); then
        printf '%s\n' 'error: --baseline requires a Git revision' >&2
        exit 2
      fi
      baseline=$2
      shift 2
      ;;
    --repo)
      if (($# < 2)); then
        printf '%s\n' 'error: --repo requires a path' >&2
        exit 2
      fi
      repository=$2
      shift 2
      ;;
    --ledger)
      if (($# < 2)); then
        printf '%s\n' 'error: --ledger requires a path' >&2
        exit 2
      fi
      ledger=$2
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      printf 'error: unsupported argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z $ledger ]]; then
  printf '%s\n' 'error: --ledger is required' >&2
  exit 2
fi
if [[ -z $baseline ]]; then
  printf '%s\n' 'error: --baseline is required; pass the resolved comprehensive-audit OID' >&2
  exit 2
fi
if [[ ! -f $ledger ]]; then
  printf 'error: ledger is not a regular file: %s\n' "$ledger" >&2
  exit 2
fi

script_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
audit_tmp=$(mktemp -d)
trap 'rm -rf -- "$audit_tmp"' EXIT

LC_ALL=C "$script_root/list-test-identities.sh" --baseline "$baseline" --repo "$repository" | LC_ALL=C sort > "$audit_tmp/baseline.tsv"
LC_ALL=C "$script_root/list-test-identities.sh" --worktree --repo "$repository" | LC_ALL=C sort > "$audit_tmp/worktree.tsv"
LC_ALL=C comm -23 "$audit_tmp/baseline.tsv" "$audit_tmp/worktree.tsv" > "$audit_tmp/removed.tsv"

awk -F '\t' '
  BEGIN {
    expected_header = "baseline-path\ttest-name\tdisposition\treplacement-path\treplacement-test\tproduction-capability-removal\tevidence"
  }
  FILENAME == ARGV[1] {
    removed[$1 SUBSEP $2] = 1
    next
  }
  FILENAME == ARGV[2] {
    current[$1 SUBSEP $2] = 1
    next
  }
  FNR == 1 {
    if ($0 != expected_header) {
      print "error: ledger header does not match the required seven-column schema" > "/dev/stderr"
      failed = 1
    }
    next
  }
  {
    if (NF != 7) {
      printf "error: ledger line %d has %d fields; expected 7\n", FNR, NF > "/dev/stderr"
      failed = 1
      next
    }

    baseline_key = $1 SUBSEP $2
    if (!(baseline_key in removed)) {
      printf "error: stale ledger identity at line %d: %s :: %s\n", FNR, $1, $2 > "/dev/stderr"
      failed = 1
      next
    }
    covered[baseline_key] = 1

    if ($3 == "replaced") {
      replacement_key = $4 SUBSEP $5
      if ($4 == "-" || $5 == "-" || !(replacement_key in current)) {
        printf "error: replacement at line %d is not an existing worktree test: %s :: %s\n", FNR, $4, $5 > "/dev/stderr"
        failed = 1
      }
      if ($6 != "-") {
        printf "error: replaced ledger line %d must use - for production-capability-removal\n", FNR > "/dev/stderr"
        failed = 1
      }
      if ($7 == "" || $7 == "-" || $7 ~ /TODO/) {
        printf "error: replaced ledger line %d lacks assertion-parity evidence\n", FNR > "/dev/stderr"
        failed = 1
      }
    } else if ($3 == "intentionally-retired") {
      if ($4 != "-" || $5 != "-") {
        printf "error: intentionally-retired ledger line %d must not claim a replacement\n", FNR > "/dev/stderr"
        failed = 1
      }
      if ($6 == "" || $6 == "-" || $6 ~ /TODO/) {
        printf "error: intentionally-retired ledger line %d lacks a production capability removal\n", FNR > "/dev/stderr"
        failed = 1
      }
      if ($7 == "" || $7 == "-" || $7 ~ /TODO/) {
        printf "error: intentionally-retired ledger line %d lacks source evidence\n", FNR > "/dev/stderr"
        failed = 1
      }
    } else {
      printf "error: unsupported disposition at line %d: %s\n", FNR, $3 > "/dev/stderr"
      failed = 1
    }
  }
  END {
    for (baseline_key in removed) {
      if (!(baseline_key in covered)) {
        split(baseline_key, identity, SUBSEP)
        printf "error: removed test has no ledger disposition: %s :: %s\n", identity[1], identity[2] > "/dev/stderr"
        failed = 1
      }
    }
    exit failed
  }
' "$audit_tmp/removed.tsv" "$audit_tmp/worktree.tsv" "$ledger"

printf 'verified test-parity ledger for %s against %s\n' "$repository" "$baseline"
