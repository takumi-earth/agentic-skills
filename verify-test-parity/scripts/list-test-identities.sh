#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf '%s\n' \
    'usage: list-test-identities.sh (--baseline REF | --worktree) [--repo PATH]' \
    '' \
    'Print normalized TAB-separated Rust test identities as: path<TAB>test-name.'
}

mode=''
baseline=''
repository='.'

while (($# > 0)); do
  case "$1" in
    --baseline)
      if (($# < 2)); then
        printf '%s\n' 'error: --baseline requires a Git revision' >&2
        exit 2
      fi
      mode='baseline'
      baseline=$2
      shift 2
      ;;
    --worktree)
      mode='worktree'
      shift
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

if [[ -z $mode ]]; then
  printf '%s\n' 'error: choose exactly one of --baseline or --worktree' >&2
  exit 2
fi

repository_root=$(git -C "$repository" rev-parse --show-toplevel)

emit_tests() {
  local source_path=$1
  if [[ $source_path == *$'\t'* || $source_path == *$'\n'* ]]; then
    printf 'error: test inventory cannot represent path containing TAB or newline: %q\n' "$source_path" >&2
    exit 1
  fi
  TEST_SOURCE_PATH=$source_path perl -0777 -ne '
    while (
      /\#\[\s*(?:(?:[A-Za-z_][A-Za-z0-9_]*)::)*test(?:\s*\([^\]]*\))?\s*\]
       \s*(?:\#\[[^\]]+\]\s*)*
       (?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)/gx
    ) {
      print "$ENV{TEST_SOURCE_PATH}\t$1\n";
    }
  '
}

if [[ $mode == 'baseline' ]]; then
  git -C "$repository_root" cat-file -e "$baseline^{tree}"
  while IFS= read -r -d '' source_path; do
    [[ $source_path == *.rs ]] || continue
    git -C "$repository_root" show "$baseline:$source_path" | emit_tests "$source_path"
  done < <(git -C "$repository_root" ls-tree -r -z --name-only "$baseline")
else
  while IFS= read -r -d '' source_path; do
    [[ -f "$repository_root/$source_path" ]] || continue
    emit_tests "$source_path" < "$repository_root/$source_path"
  done < <(git -C "$repository_root" ls-files -z --cached --others --exclude-standard -- '*.rs')
fi
