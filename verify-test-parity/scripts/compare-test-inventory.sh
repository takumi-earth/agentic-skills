#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf '%s\n' \
    'usage: compare-test-inventory.sh [--baseline REF] [--repo PATH]' \
    '' \
    'Print a TAB-separated removed/moved/globally-missing/added Rust test inventory.'
}

baseline='HEAD'
repository='.'

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

script_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
audit_tmp=$(mktemp -d)
trap 'rm -rf -- "$audit_tmp"' EXIT

LC_ALL=C "$script_root/list-test-identities.sh" --baseline "$baseline" --repo "$repository" | LC_ALL=C sort > "$audit_tmp/baseline.tsv"
LC_ALL=C "$script_root/list-test-identities.sh" --worktree --repo "$repository" | LC_ALL=C sort > "$audit_tmp/worktree.tsv"
LC_ALL=C comm -23 "$audit_tmp/baseline.tsv" "$audit_tmp/worktree.tsv" > "$audit_tmp/removed.tsv"
LC_ALL=C comm -13 "$audit_tmp/baseline.tsv" "$audit_tmp/worktree.tsv" > "$audit_tmp/added.tsv"

printf '%s\n' $'category\tbaseline-path\ttest-name\tworktree-path'

while IFS=$'\t' read -r baseline_path test_name; do
  [[ -n $baseline_path ]] || continue
  printf 'removed\t%s\t%s\t-\n' "$baseline_path" "$test_name"

  moved=false
  while IFS=$'\t' read -r worktree_path worktree_name; do
    [[ $worktree_name == "$test_name" ]] || continue
    printf 'moved-candidate\t%s\t%s\t%s\n' "$baseline_path" "$test_name" "$worktree_path"
    moved=true
  done < "$audit_tmp/worktree.tsv"

  if [[ $moved == false ]]; then
    printf 'globally-missing\t%s\t%s\t-\n' "$baseline_path" "$test_name"
  fi
done < "$audit_tmp/removed.tsv"

while IFS=$'\t' read -r worktree_path test_name; do
  [[ -n $worktree_path ]] || continue
  printf 'added\t-\t%s\t%s\n' "$test_name" "$worktree_path"
done < "$audit_tmp/added.tsv"
