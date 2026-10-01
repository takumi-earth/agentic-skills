# Complete instruction reads

Build the exact list of trigger-matched `SKILL.md` files and directly required resources before reading their bodies. Do not load unrelated skills merely because they may be useful later.

When more than one instruction file is required:

1. Preflight the entire selected set together. Run one `python3 scripts/plan_instruction_reads.py <path>...` invocation from the skill package root, or use parallel metadata-only calls when a different preflight tool is appropriate. Batch or aggregate existence, logical line counts, byte counts, hashes, and range plans because they contain no instruction bodies. Do not serialize one `wc`, hash, or planner command per file.
2. Read exactly one planned file range in each tool result. Never concatenate files, print several bodies from one command, or combine parallel reads into one orchestration result; aggregate output limits can truncate the composed result even when each nested call has a larger limit.
3. Maintain a small ledger containing `path`, `sha256`, `final_line`, `next_line`, and `complete`. Advance `next_line` only through visibly complete output, and mark a file complete only when the final planned range reaches `final_line` without truncation.
4. If a result is truncated, preserve every earlier confirmed range and resume that file at the first unread line. Do not restart the file or reread complete siblings from the attempted batch.
5. Re-run the planner after all reads when the files may have changed concurrently. If a hash changed, discard only that file's stale ledger entry and read its new plan; do not invalidate unchanged files.

The planner uses LF-delimited line addressing, matching `sed -n 'START,ENDp'`: CRLF bytes remain intact, bare CR does not advance the line, and an unterminated final line counts. An empty file has no body ranges. It flags a single line whose bytes exceed the chosen chunk limit. For an oversized line, read that line alone with a sufficiently bounded one-file result; never hide it inside a larger aggregate. Apply the same protocol to directly referenced skill instructions.
